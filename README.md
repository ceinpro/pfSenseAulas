# Panel de control de Internet por aula

**Versión 1.1.0 · GPL-3.0-only**

Panel para centros educativos que permite o bloquea Internet por aula mediante reglas de pfSense y pfREST v2. Interfaz en castellano y euskera, con contraseña, HTTPS y protección CSRF. Utiliza Python, Flask y Docker Compose.

## Configuración por centro

- Nombre del centro y aulas en **`config/settings.json`**.
- Aulas configurables: nombre, traducción opcional al euskera, tracker y alias de equipos.
- URL de pfSense, interfaz y destino de las reglas configurables. Se permiten criterios diferentes por aula, por ejemplo para VLAN distintas.
- IP y puerto del panel en **`.env`**.
- Instalación en una ruta genérica, por ejemplo **`/opt/panel-aulas`**.
- Instalador interactivo sin direcciones ni trackers propios de un centro. Las aulas se crean sin vincular a reglas.

Consulta [LEEME.md](LEEME.md) para la instalación completa, configuración de aulas, actualización y migración desde ZIP. [settings.example.json](settings.example.json) muestra la estructura de personalización sin secretos; [.env.example](.env.example) muestra las opciones de red.

## Instalación desde GitHub

Con los requisitos del manual instalados, ejecuta como root:

```bash
git clone https://github.com/ceinpro/pfSenseAulas.git /opt/panel-aulas
cd /opt/panel-aulas
python3 setup.py
docker compose up -d --build
```

El asistente genera la configuración privada. Vincula las aulas con reglas reales desde `config/settings.json`. Por defecto, Docker solo publica el servicio en `127.0.0.1`; elige la IP de administración del servidor en el asistente o en `.env` para acceso remoto.

## Actualización

Conserva **`config/` y `.env`**. No vuelvas a ejecutar el asistente. Revisa cambios locales y crea una copia de seguridad como indica el manual antes de ejecutar:

```bash
cd /opt/panel-aulas
git pull --ff-only && docker compose up -d --build
docker compose ps
docker compose logs --tail=50
```

Si actualizas desde la versión 1.0, conserva la carpeta original y crea `.env` con su IP y puerto actuales **antes de actualizar**. Si faltan los criterios de firewall en una configuración antigua, se conservan los de la versión 1.0; añade los valores explícitos siguiendo el manual. No hace falta regenerar claves, contraseñas ni aulas.

## Funcionamiento y límites

El panel identifica cada regla por tracker, valida origen, destino, interfaz y tipo, cambia el bloqueo, aplica y comprueba el resultado. La clave API permanece en el servidor. Solo acepta reglas IPv4 de bloqueo o rechazo previamente creadas; no crea ni reordena reglas. No elimina estados de conexiones abiertas y el estado mostrado no equivale a una prueba de conectividad desde cada equipo.

No incorpora Active Directory. Muestra confirmaciones visuales y no reproduce sonidos.

## Código y licencia

Repositorio: https://github.com/ceinpro/pfSenseAulas. Consulta [PUBLICAR.md](PUBLICAR.md) para publicar una copia del código sin configuración privada. Subir código no despliega el panel en el servidor.

Copyright (C) 2026 CEINPRO. Distribuido bajo la **GNU General Public License, versión 3 (GPL-3.0-only)**. Consulta [LICENSE](LICENSE). La atribución del autor no determina el nombre mostrado por el panel: cada centro lo configura en `center_name`.
