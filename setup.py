#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 CEINPRO
import getpass
import hashlib
import json
import os
import secrets
import ssl
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

os.chdir(Path(__file__).resolve().parent)
folder = Path('config')
if folder.exists():
    raise SystemExit('Ya existe config. Conserva su contenido. Para arrancar usa docker compose up -d --build.')
key = getpass.getpass('Clave API de pfSense: ').strip()
if not key:
    raise SystemExit('La clave está vacía.')
password = getpass.getpass('Contraseña nueva para entrar al panel (mínimo 12 caracteres): ')
if len(password) < 12:
    raise SystemExit('La contraseña necesita al menos 12 caracteres.')
if getpass.getpass('Repite la contraseña del panel: ') != password:
    raise SystemExit('Las contraseñas no coinciden.')
url = 'https://pfsense.ceinpro.es'
print('Comprobando conexión y lectura de reglas...')
req = urllib.request.Request(url + '/api/v2/firewall/rules', headers={'X-API-Key': key})
try:
    with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=20) as response:
        payload = json.load(response)
    matches = [r for r in payload.get('data', []) if str(r.get('tracker')) == '1794910814']
    if payload.get('status') != 'ok' or len(matches) != 1:
        raise ValueError('No se encuentra una única regla del Aula 9.')
except (urllib.error.URLError, ValueError) as error:
    raise SystemExit('No se ha podido validar la conexión o la regla. Revisa certificado, DNS y clave. ' + str(error))

salt = secrets.token_hex(16)
digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
classrooms = [{'id': n, 'name': 'Aula ' + str(n), 'tracker': None} for n in range(1, 16)]
classrooms[8].update(tracker='1794910814', source='PC_Aula09')
settings = {'pfsense_url': url, 'password_hash': 'pbkdf2:sha256:600000$' + salt + '$' + digest,
            'classrooms': classrooms}
os.umask(0o077)
folder.mkdir(mode=0o750)
(folder / 'settings.json').write_text(json.dumps(settings, indent=2) + '\n')
(folder / 'api-key').write_text(key + '\n')
(folder / 'session-key').write_text(secrets.token_urlsafe(48) + '\n')
subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-sha256', '-days', '365', '-nodes',
                '-keyout', str(folder / 'tls.key'), '-out', str(folder / 'tls.crt'),
                '-subj', '/CN=ceinpro-aulas', '-addext', 'subjectAltName=IP:192.168.30.174,DNS:localhost'], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for path in [folder] + list(folder.iterdir()):
    os.chown(path, 10001, 10001)
    os.chmod(path, 0o750 if path.is_dir() else 0o640)
print('Configuración guardada. Ejecuta docker compose up -d --build')
print('Panel disponible tras el arranque en https://192.168.30.174:8445')
