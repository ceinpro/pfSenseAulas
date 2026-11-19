import functools
import json
import logging
import os
import secrets
import threading
import time
from datetime import timedelta
from pathlib import Path

import requests
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from translations import EU, classroom_name, language, translate as t

CONFIG_DIR = Path(os.environ.get('CONFIG_DIR', '/config'))
CONFIG = json.loads((CONFIG_DIR / 'settings.json').read_text())
API_KEY = (CONFIG_DIR / 'api-key').read_text().strip()
app = Flask(__name__)
app.secret_key = (CONFIG_DIR / 'session-key').read_text().strip()
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Strict', PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
                  MAX_CONTENT_LENGTH=4096)
change_lock = threading.Lock()
login_lock = threading.Lock()
login_attempts = []
logging.basicConfig(level=logging.INFO)


class FirewallError(Exception):
    def __str__(self):
        return t(super().__str__())


def firewall(method, path, body=None):
    try:
        response = requests.request(
            method, CONFIG['pfsense_url'].rstrip('/') + '/api/v2/' + path,
            headers={'X-API-Key': API_KEY}, json=body,
            timeout=(8, 65), allow_redirects=False,
            verify=CONFIG.get('ca_bundle') or True,
        )
        if response.status_code != 200:
            raise FirewallError(t('pfSense responde HTTP {status}. Revisa permisos y conexión.').format(status=response.status_code))
        payload = response.json()
        if payload.get('status') != 'ok':
            raise FirewallError('pfSense no ha confirmado la operación.')
        return payload['data']
    except requests.exceptions.SSLError as error:
        raise FirewallError('No se puede validar el certificado HTTPS de pfSense.') from error
    except (requests.RequestException, ValueError, KeyError) as error:
        raise FirewallError('No se ha podido confirmar la respuesta de pfSense. Actualiza antes de repetir el cambio.') from error


def find_rule(rules, classroom):
    matches = [r for r in rules if str(r.get('tracker')) == str(classroom['tracker'])]
    if len(matches) != 1:
        raise FirewallError('No se encuentra una única regla para esta aula.')
    rule = matches[0]
    if (rule.get('source') != classroom['source'] or rule.get('interface') != ['lan']
            or rule.get('type') not in ('block', 'reject')
            or rule.get('destination') != '!Sare_pribatuak'
            or rule.get('ipprotocol') != 'inet'
            or type(rule.get('disabled')) is not bool):
        raise FirewallError('La regla del aula ha cambiado. Revisa origen, destino, interfaz y tipo en pfSense.')
    return rule


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('authenticated'):
            if request.path.startswith('/api/'):
                return jsonify(error=t('La sesión ha caducado. Vuelve a entrar.')), 401
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


@app.before_request
def protect_changes():
    if request.method == 'POST':
        expected = session.get('csrf', '')
        provided = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
        if not expected or not secrets.compare_digest(expected, provided):
            return jsonify(error=t('Sesión inválida. Recarga la página.')), 403


@app.after_request
def headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.setdefault('csrf', secrets.token_urlsafe(32))
    error = None
    if request.method == 'POST':
        with login_lock:
            now = time.monotonic()
            login_attempts[:] = [t for t in login_attempts if now - t < 300]
            if len(login_attempts) >= 15:
                return render_template('login.html', error=t('Espera cinco minutos antes de volver a intentarlo.')), 429
            valid = check_password_hash(CONFIG['password_hash'], request.form.get('password', ''))
            if valid:
                login_attempts.clear()
            else:
                login_attempts.append(now)
        if valid:
            session.clear()
            session.update(authenticated=True, csrf=secrets.token_urlsafe(32))
            session.permanent = True
            return redirect(url_for('index'))
        error = t('La contraseña no es correcta.')
    return render_template('login.html', error=error)


@app.post('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.get('/')
@login_required
def index():
    return render_template('index.html', classrooms=CONFIG['classrooms'])


@app.get('/api/status')
@login_required
def status():
    try:
        with change_lock:
            rules = firewall('GET', 'firewall/rules')
            applied = firewall('GET', 'firewall/apply').get('applied') is True
            classrooms = []
            for classroom in CONFIG['classrooms']:
                if not classroom.get('tracker'):
                    classrooms.append(dict(id=classroom['id'], state='unconfigured'))
                    continue
                try:
                    rule = find_rule(rules, classroom)
                    state = 'blocked' if not rule['disabled'] else 'allowed'
                    classrooms.append(dict(id=classroom['id'], state=state if applied else 'pending'))
                except FirewallError as error:
                    classrooms.append(dict(id=classroom['id'], state='error', error=str(error)))
        return jsonify(classrooms=classrooms, applied=applied)
    except FirewallError as error:
        return jsonify(error=str(error)), 502


@app.post('/api/classrooms/<int:classroom_id>')
@login_required
def change(classroom_id):
    classroom = next((c for c in CONFIG['classrooms'] if c['id'] == classroom_id and c.get('tracker')), None)
    if classroom is None:
        return jsonify(error=t('Aula sin configurar.')), 404
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict) or type(body.get('blocked')) is not bool or type(body.get('expected_blocked')) is not bool:
        return jsonify(error=t('Solicitud inválida.')), 400
    changed = False
    try:
        with change_lock:
            if firewall('GET', 'firewall/apply').get('applied') is not True:
                raise FirewallError('Hay cambios pendientes en pfSense. Revísalos y aplícalos en su interfaz antes de continuar.')
            rules = firewall('GET', 'firewall/rules')
            rule = find_rule(rules, classroom)
            current = not rule['disabled']
            if current != body['expected_blocked']:
                return jsonify(error=t('El estado ha cambiado desde otra sesión. Actualiza antes de continuar.')), 409
            if current != body['blocked']:
                # Recheck the current index immediately before PATCH. IDs change on reorder.
                fresh = firewall('GET', 'firewall/rule?id=' + str(rule['id']))
                if str(fresh.get('tracker')) != str(classroom['tracker']):
                    raise FirewallError('Las reglas se han reordenado. Actualiza y vuelve a intentarlo.')
                changed = True
                firewall('PATCH', 'firewall/rule', {
                    'id': rule['id'], 'disabled': not body['blocked'], 'apply': False,
                })
                firewall('POST', 'firewall/apply', {'async': False})
                if firewall('GET', 'firewall/apply').get('applied') is not True:
                    raise FirewallError('pfSense mantiene cambios pendientes de aplicar.')
                confirmed = find_rule(firewall('GET', 'firewall/rules'), classroom)
                if (not confirmed['disabled']) != body['blocked']:
                    raise FirewallError('El estado final de la regla no coincide con el solicitado.')
            app.logger.info('aula=%s bloqueo=%s cliente=%s', classroom_id, body['blocked'], request.remote_addr)
        return jsonify(ok=True)
    except FirewallError as error:
        message = str(error)
        if changed:
            message += t(' La configuración puede haberse guardado. Comprueba la regla y Apply Changes en pfSense antes de repetir.')
        return jsonify(error=message), 502


@app.context_processor
def localization():
    return dict(t=t, lang=language(), classroom_name=classroom_name,
                translations=EU if language() == 'eu' else {})


@app.get('/language/<lang>')
def set_language(lang):
    if lang not in ('es', 'eu'):
        return '', 404
    response = redirect(url_for('index' if session.get('authenticated') else 'login'))
    response.set_cookie('language', lang, max_age=31536000, secure=True,
                        httponly=True, samesite='Strict')
    return response
