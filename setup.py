#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 CEINPRO
"""Asistente inicial. No modifica una instalación ya configurada."""
import getpass
import hashlib
import ipaddress
import json
import os
import re
import secrets
import ssl
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def hostname(value):
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        if len(value) > 253 or not all(
            re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?', label)
            for label in value.split('.')
        ):
            raise ValueError('Introduce una IP o un nombre DNS válido, sin https:// ni puerto.')
        return value.lower()


def main():
    os.chdir(Path(__file__).resolve().parent)
    folder = Path('config')
    if folder.exists():
        raise SystemExit('Ya existe config. Conserva su contenido. Para arrancar usa docker compose up -d --build.')
    if Path('.env').exists():
        raise SystemExit('Ya existe .env. Consérvalo y revisa sus ajustes antes de la instalación inicial.')
    center_name = input('Nombre del centro educativo: ').strip()
    if not center_name:
        raise SystemExit('El nombre del centro no puede estar vacío.')
    url = input('URL HTTPS de pfSense (ejemplo: https://firewall.example.org): ').strip().rstrip('/')
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment):
        raise SystemExit('Introduce únicamente una URL HTTPS de pfSense, sin rutas ni credenciales.')
    try:
        panel_host = hostname(input('IP o nombre DNS para acceder al panel: ').strip())
        bind_address = str(ipaddress.ip_address(input('IP local donde publicar el panel [127.0.0.1]: ').strip() or '127.0.0.1'))
        port = int(input('Puerto HTTPS del panel [8445]: ').strip() or '8445')
        count = int(input('Número inicial de aulas [1]: ').strip() or '1')
        if not 1 <= port <= 65535 or not 1 <= count <= 1000:
            raise ValueError('Puerto: 1–65535. Número de aulas: 1–1000.')
    except ValueError as error:
        raise SystemExit(str(error))
    interface = input('Interfaz pfSense de las reglas (identificador interno) [lan]: ').strip() or 'lan'
    alias = input('Alias pfSense que agrupa las redes internas [REDES_INTERNAS]: ').strip() or 'REDES_INTERNAS'
    if not re.fullmatch(r'[a-zA-Z0-9_]+', alias):
        raise SystemExit('El alias solo puede contener letras, números y guiones bajos.')
    ca_path = input('Ruta absoluta al certificado CA de pfSense, si usa una CA privada [CA del sistema]: ').strip()
    if ca_path and (not Path(ca_path).is_absolute() or not Path(ca_path).is_file()):
        raise SystemExit('La ruta CA debe ser absoluta y apuntar a un archivo existente.')
    key = getpass.getpass('Clave API de pfSense: ').strip()
    if not key:
        raise SystemExit('La clave está vacía.')
    password = getpass.getpass('Contraseña nueva para entrar al panel (mínimo 12 caracteres): ')
    if len(password) < 12:
        raise SystemExit('La contraseña necesita al menos 12 caracteres.')
    if getpass.getpass('Repite la contraseña del panel: ') != password:
        raise SystemExit('Las contraseñas no coinciden.')
    print('Comprobando conexión y lectura de reglas...')
    req = urllib.request.Request(url + '/api/v2/firewall/rules', headers={'X-API-Key': key})
    try:
        context = ssl.create_default_context(cafile=ca_path or None)
        with urllib.request.urlopen(req, context=context, timeout=20) as response:
            payload = json.load(response)
        if payload.get('status') != 'ok' or not isinstance(payload.get('data'), list):
            raise ValueError('La API no devuelve una lista de reglas válida.')
    except (urllib.error.URLError, ValueError, OSError) as error:
        raise SystemExit('No se ha podido validar la conexión. Revisa certificado, DNS y clave. ' + str(error))
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
    classrooms = [{'id': n, 'name': 'Aula ' + str(n), 'tracker': None} for n in range(1, count + 1)]
    settings = {'center_name': center_name, 'pfsense_url': url,
                'password_hash': 'pbkdf2:sha256:600000$' + salt + '$' + digest,
                'firewall': {'interface': [interface], 'destination': '!' + alias},
                'classrooms': classrooms}
    os.umask(0o077)
    folder.mkdir(mode=0o750)
    if ca_path:
        (folder / 'pfsense-ca.crt').write_bytes(Path(ca_path).read_bytes())
        settings['ca_bundle'] = '/config/pfsense-ca.crt'
    (folder / 'settings.json').write_text(json.dumps(settings, indent=2, ensure_ascii=False) + '\n')
    (folder / 'api-key').write_text(key + '\n')
    (folder / 'session-key').write_text(secrets.token_urlsafe(48) + '\n')
    try:
        ipaddress.ip_address(panel_host)
        san = 'IP:' + panel_host
    except ValueError:
        san = 'DNS:' + panel_host
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-sha256', '-days', '365', '-nodes',
                    '-keyout', str(folder / 'tls.key'), '-out', str(folder / 'tls.crt'),
                    '-subj', '/CN=panel-aulas', '-addext', 'subjectAltName=' + san], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for path in [folder] + list(folder.iterdir()):
        os.chown(path, 10001, 10001)
        os.chmod(path, 0o750 if path.is_dir() else 0o640)
    # Brackets preserve IPv6 addresses in Compose port mappings.
    bind_value = '[' + bind_address + ']' if ':' in bind_address else bind_address
    Path('.env').write_text(f'PANEL_BIND_ADDRESS={bind_value}\nPANEL_PORT={port}\n')
    display_host = '[' + panel_host + ']' if ':' in panel_host else panel_host
    print('Configuración guardada. Vincula las aulas en config/settings.json y ejecuta docker compose up -d --build')
    print(f'URL de acceso: https://{display_host}:{port}')
    if bind_address in ('127.0.0.1', '::1'):
        print('El panel solo escucha en el servidor. Para acceso remoto, configura PANEL_BIND_ADDRESS en .env con su IP de administración.')


if __name__ == '__main__':
    main()
