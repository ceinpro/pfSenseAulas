# CEINPRO · Control de Internet

**Versión 1.0.0 · GPL-3.0-only**

Panel interno para permitir o bloquear la salida a Internet por aula mediante reglas de pfSense y pfREST v2.

La interfaz está disponible en **castellano y euskera**, con selector **ES / EU** en el acceso y en la cabecera. La preferencia se recuerda mediante una cookie; si no hay elección, se utiliza el idioma del navegador cuando es compatible.

La versión actual utiliza Python, Flask y Docker Compose. Muestra tarjetas compactas con el estado del aula y un único botón: **Bloquear** o **Permitir**. Esta versión todavía no incorpora integración con Active Directory ni Razor Pages.

## Puesta en marcha

Consulta [LEEME.md](LEEME.md) para los requisitos, la configuración inicial y el mantenimiento.

```bash
python3 setup.py
docker compose up -d --build
```

El asistente solicita las credenciales de forma interactiva y genera la carpeta privada `config/`. No se incluye en el repositorio.

## Funcionamiento

- Localiza cada regla mediante su tracker, sin guardar el índice posicional como identificador permanente.
- Valida el origen, destino, interfaz y tipo antes de cambiar el bloqueo.
- Aplica los cambios y comprueba la respuesta de pfSense.
- Mantiene la clave API en el servidor.
- Incluye contraseña de acceso, protección CSRF y HTTPS.

El proyecto conserva los valores de la instalación de CEINPRO: servidor Docker `192.168.30.174`, pfSense `pfsense.ceinpro.es` y la regla del Aula 9. Para otra instalación hay que adaptar `setup.py`, `compose.yaml` y la validación de reglas de `app.py`.

## Límites actuales

Controla reglas IPv4. No elimina los estados de conexiones existentes. El estado de la tarjeta representa la configuración confirmada del firewall, no una prueba de conectividad desde cada equipo. Solo el Aula 9 viene vinculada a una regla; las demás requieren configuración.

## Publicar el código

Consulta [PUBLICAR.md](PUBLICAR.md). `.gitignore` excluye la configuración privada, certificados con clave privada, entornos Python y archivos temporales.

## Repositorio

https://github.com/ceinpro/pfSenseAulas

## Licencia

Copyright (C) 2026 CEINPRO. Este proyecto se distribuye bajo la **GNU General Public License, versión 3 (GPL-3.0-only)**. Consulta el texto completo en [LICENSE](LICENSE).

## Actualizar una instalación

Actualizar GitHub no actualiza automáticamente el servidor Docker. Si la instalación es un clon de este repositorio, descarga los cambios con `git pull --ff-only`; si se instaló desde un ZIP, sustituye los archivos del código por los de la última versión. Conserva siempre la carpeta privada `config/`. Después ejecuta:

```bash
cd /opt/ceinpro-aulas
docker compose up -d --build
```

No vuelvas a ejecutar `setup.py` en una instalación configurada. La versión debe aparecer junto al título y el selector **ES / EU**, en la cabecera y en la pantalla de acceso.
