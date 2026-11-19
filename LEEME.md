# Panel de control de Internet por aula

Aplicación para centros educativos que permite o bloquea Internet mediante reglas existentes de pfSense y pfREST v2. Cada centro configura su nombre, sus aulas y su conexión con el firewall, sin modificar el código.

## Requisitos

- Servidor Linux con Git, Python 3, OpenSSL y Docker Engine con Docker Compose.
- pfSense con pfREST v2 y certificado HTTPS válido para el nombre utilizado. Si utiliza una CA privada, el asistente permite importar su certificado público.
- Clave API con permisos para GET `/api/v2/firewall/rules`, GET/PATCH `/api/v2/firewall/rule` y GET/POST `/api/v2/firewall/apply`.
- Alias de equipos por aula, alias de redes internas y reglas de bloqueo IPv4 previamente creadas y probadas en pfSense.

Comprueba las herramientas del servidor:

```bash
git --version
python3 --version
openssl version
docker compose version
```

## Instalación desde GitHub

Ejecuta como root en el servidor. `/opt/panel-aulas` es una ruta genérica: puedes elegir otra carpeta. No ejecutes esta instalación inicial sobre una carpeta que ya contenga configuración.

```bash
git clone https://github.com/ceinpro/pfSenseAulas.git /opt/panel-aulas
cd /opt/panel-aulas
python3 setup.py
```

El asistente pide nombre del centro, URL de pfSense, IP o nombre DNS de acceso al panel, IP local donde publicar el servicio, puerto, número inicial de aulas, interfaz de pfSense y alias de redes internas. También solicita la clave API, una contraseña del panel y, opcionalmente, la ruta del certificado CA de pfSense. Comprueba la lectura de reglas, genera secretos y un certificado HTTPS autofirmado válido un año. No crea ni cambia reglas en el firewall.

El asistente guarda:

| Archivo | Contenido |
| --- | --- |
| `config/settings.json` | Nombre del centro, pfSense, criterios de reglas y lista de aulas; incluye el hash de contraseña. |
| `config/api-key` | Clave privada de acceso a la API. |
| `config/session-key` | Clave privada de sesión del panel. |
| `config/tls.crt` y `config/tls.key` | Certificado y clave HTTPS del panel. |
| `config/pfsense-ca.crt` | Certificado CA de pfSense, si se proporcionó. |
| `.env` | IP de escucha y puerto de publicación de Docker. |

Las aulas nuevas aparecen **Sin configurar** hasta que se vinculan con sus reglas. Configúralas como se explica más abajo y arranca:

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=50
```

Abre `https://IP_O_DNS_DEL_PANEL:PUERTO` con los valores elegidos. La IP de escucha predeterminada es `127.0.0.1`: solo permite conexiones desde el servidor. Para acceso remoto utiliza en `.env` la IP local de administración del servidor, que debe pertenecer a una interfaz del host. Si cambias `.env`, ejecuta de nuevo `docker compose up -d`.

El navegador advertirá del certificado autofirmado. Puedes confiar en `config/tls.crt` desde los equipos de administración o sustituir `tls.crt`/`tls.key` por un certificado de vuestra CA que incluya el nombre DNS o IP de acceso. Restringe el acceso a la API de pfSense al servidor del panel. Las claves API heredan los privilegios del usuario que las genera.

## Nombre del centro y aulas

Edita **`config/settings.json`**. El nombre del centro aparece en el acceso, la cabecera y el título del navegador:

```json
"center_name": "Mi centro educativo"
```

Las aulas están en la lista **`classrooms`** del mismo archivo. Puedes añadir, quitar, reordenar y renombrar las entradas. No hay una lista fija de 15 aulas en el programa. Por ejemplo, una entrada ya vinculada a una regla real:

```json
{
  "id": 1,
  "name": "Aula de informática",
  "name_eu": "Informatika gela",
  "tracker": "TRACKER_REAL_DE_PFSENSE",
  "source": "EQUIPOS_INFORMATICA"
}
```

| Campo | Uso |
| --- | --- |
| `id` | Entero positivo único y estable dentro del panel. No es el índice de la regla de pfSense. |
| `name` | Nombre visible del aula. |
| `name_eu` | Nombre opcional en euskera. Si falta, se conserva el nombre; `Aula N` se traduce automáticamente. |
| `tracker` | Tracker real de la regla de bloqueo de pfSense, como cadena. Usa `null` para aulas sin vincular. |
| `source` | Origen exacto de la regla, normalmente el alias del aula. Obligatorio si hay tracker. |
| `interface` | Lista opcional de interfaces internas de pfSense para esa aula. Si falta, utiliza el valor general. |
| `destination` | Destino opcional exacto de esa regla. Si falta, utiliza el valor general. |

Los valores generales están en `firewall`:

```json
"firewall": {
  "interface": ["lan"],
  "destination": "!REDES_INTERNAS"
}
```

`lan` es el identificador interno de pfSense, no su etiqueta visible. Para una VLAN puede ser `opt1` u otro identificador: consulta el valor real devuelto por pfREST. El destino `!REDES_INTERNAS` significa que la regla afecta a los destinos fuera del alias de redes internas. Configura ese alias con todas las redes del centro cuyo acceso deba mantenerse.

Crea y prueba las reglas en pfSense antes de vincularlas. El panel solo acepta reglas IPv4 de bloqueo o rechazo cuyo origen, destino e interfaz coincidan con la configuración. No crea ni reordena reglas ni deduce trackers a partir del número de aula.

`settings.example.json` muestra la estructura sin secretos. **No sustituye un `settings.json` completo**: no incluye el hash de contraseña generado por el asistente. Al editar una instalación existente, conserva los campos y secretos presentes.

Después de modificar `config/settings.json`:

```bash
cd /opt/panel-aulas
python3 -m json.tool config/settings.json > /dev/null && docker compose restart
```

El reinicio vuelve a leer la configuración. Si trabajas con un editor que reemplaza el archivo, conserva su propietario `10001:10001` y permisos `640`, y los permisos `750` del directorio `config/`.

## Comprobación del funcionamiento

Entra al panel, verifica el estado de un aula configurada y pulsa **Bloquear**. Comprueba una conexión nueva desde uno de sus equipos y el acceso a los recursos internos. Pulsa **Permitir** y verifica la restauración. Comprueba también que los equipos fuera del alias no se ven afectados.

El panel localiza la regla por tracker, comprueba origen, destino, interfaz y tipo, cambia únicamente `disabled`, aplica los cambios y verifica el resultado. Solo controla IPv4. Las conexiones abiertas pueden continuar hasta que caduquen o se eliminen sus estados; el panel no los elimina. El estado mostrado representa la regla aplicada, no una prueba de conectividad desde cada PC.

Si hay cambios pendientes en pfSense, revísalos y aplícalos desde su interfaz antes de usar el panel. Apply afecta a las modificaciones pendientes del firewall. Si una operación muestra **Sin confirmar**, comprueba la regla y Apply Changes antes de repetir. Evita reordenar o editar reglas durante una operación desde el panel: los índices de la API son posicionales y no existe aquí una escritura atómica por tracker.

## Actualización desde GitHub

Publicar en GitHub no actualiza el servidor automáticamente. En una instalación existente, **conserva `config/` y `.env` y no vuelvas a ejecutar `setup.py`**.

### Preparación al actualizar desde la versión 1.0

Puedes conservar la carpeta actual: no hace falta renombrar una instalación en funcionamiento. Sustituye `/opt/panel-aulas` en los comandos por su ruta real; mantener esa carpeta también conserva el nombre del proyecto Docker Compose y evita arrancar un segundo panel.

Antes de actualizar, crea `.env` en esa carpeta con la misma IP local y puerto que utilizaba tu `compose.yaml`. Por ejemplo, reemplazando `IP_LOCAL_DEL_SERVIDOR` por el valor real:

```dotenv
PANEL_BIND_ADDRESS=IP_LOCAL_DEL_SERVIDOR
PANEL_PORT=8445
```

Sin ese ajuste, la nueva versión escucha solo en `127.0.0.1`. El puerto es configurable y debe conservarse si ya utilizabas otro.

Añade `center_name` a `config/settings.json`. Si no está, el panel muestra **Centro educativo**. Las aulas, trackers, contraseñas y claves existentes se conservan. Para compatibilidad, si faltan los criterios `firewall`, se mantienen los criterios de validación de la versión 1.0. Recomendamos añadir `firewall` con la interfaz y el destino exactos de tus reglas actuales; no cambies sus valores por los del ejemplo sin comprobarlos.

### Procedimiento habitual

Comprueba primero los cambios locales:

```bash
cd /opt/panel-aulas
git status --short
```

Si aparecen archivos modificados, revísalos y conserva los ajustes necesarios antes de continuar. No uses `git reset --hard` ni `git clean` para resolver el problema. Guarda los ajustes de IP y puerto en `.env`, que está excluido del repositorio. Para otros ajustes de Docker puedes usar `compose.override.yaml`, también excluido; revisa el resultado con `docker compose config`.

Crea una copia privada de toda la instalación, descarga la nueva versión y reconstruye. Los operadores `&&` detienen la secuencia si falla un paso:

```bash
cd /opt/panel-aulas
umask 077
tar -czf "/root/panel-aulas-backup-$(date +%Y%m%d-%H%M%S).tar.gz" -C /opt panel-aulas &&
git pull --ff-only &&
docker compose up -d --build
```

Si utilizas otra ruta, adapta tanto `cd` como los argumentos `-C` y el nombre de carpeta de `tar`. El contenedor se recrea y puede interrumpir brevemente el panel. Comprueba:

```bash
docker compose ps
docker compose logs --tail=50
cat VERSION
```

Abre el panel, pulsa Ctrl+F5 y comprueba el acceso y la consulta de estados. Si falla un comando, detente y revisa el error.

### Vincular una instalación hecha desde ZIP

`fatal: not a git repository` indica que faltan los metadatos de Git. Realiza esta vinculación una sola vez, conservando la carpeta original de la instalación:

1. Configura `.env` y el nombre del centro como se indica en la preparación anterior.
2. Crea una copia privada completa de la instalación, adaptando la ruta si es distinta:

```bash
cd /opt/panel-aulas
umask 077
tar -czf "/root/panel-aulas-backup-$(date +%Y%m%d-%H%M%S).tar.gz" -C /opt panel-aulas
```

Continúa solo si la copia finaliza correctamente.

3. Descarga un clon temporal:

```bash
repo_temporal=$(mktemp -d /opt/panel-aulas-github.XXXXXX)
git clone https://github.com/ceinpro/pfSenseAulas.git "$repo_temporal"
```

Si falla la descarga, detente. Revisa las diferencias de Docker y conserva tus personalizaciones antes de copiar:

```bash
diff -u /opt/panel-aulas/compose.yaml "$repo_temporal/compose.yaml"
```

`diff` devuelve 1 si hay diferencias. El repositorio no incluye `config/` ni `.env`. Copia el código y `.git` sobre la carpeta original y reconstruye:

```bash
cp -a "$repo_temporal"/. /opt/panel-aulas/ &&
cd /opt/panel-aulas &&
docker compose up -d --build
```

Comprueba `git status --short`, `docker compose ps` y los registros. No arranques el panel desde el clon temporal. Para las siguientes actualizaciones utiliza `git pull --ff-only` como se indica arriba.

## Mantenimiento e idiomas

```bash
cd /opt/panel-aulas
docker compose logs --tail=100
docker compose restart
docker compose down
```

Guarda una copia privada de `config/` y `.env`. Para cambiar la clave API edita `config/api-key` y reinicia. Si utilizas una CA privada, `ca_bundle` debe ser una ruta legible desde el contenedor, por ejemplo `/config/pfsense-ca.crt`. Tras actualizar pfSense, instala la versión compatible de pfREST y verifica lectura, bloqueo y restauración.

La interfaz incluye selector ES / EU. La preferencia se recuerda durante un año en una cookie. Sin selección previa se utiliza el idioma compatible del navegador o castellano. El nombre del centro no se traduce; los nombres de aulas admiten `name_eu`. Los alias y trackers no se traducen.

El panel muestra confirmaciones visuales y no reproduce sonidos.
