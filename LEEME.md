# CEINPRO · Control de Internet por aula

Instalación prevista en Heriz74, 192.168.30.174. Requiere Docker Compose, Python 3 y OpenSSL en el host. Usa pfREST v2, HTTPS con validación del certificado de pfSense y una clave API guardada en config/api-key. Solo el Aula 9 viene conectada, por tracker 1794910814 y origen PC_Aula09. El resto de tarjetas muestra Sin configurar.

## Instalación

Extrae la carpeta ceinpro-aulas en /opt y ejecuta como root:

```bash
cd /opt/ceinpro-aulas
python3 setup.py
docker compose up -d --build
docker compose logs --tail=50
```

El asistente pide la clave API y una contraseña nueva para el panel. Comprueba la lectura de la regla, genera una clave de sesión y un certificado HTTPS autofirmado válido un año. Si el puerto 8445 está ocupado, modifica el puerto del host en compose.yaml antes de arrancar.

Abre https://192.168.30.174:8445. El navegador advertirá que el certificado es autofirmado. Puedes importar el certificado config/tls.crt en los equipos de administración, o reemplazar tls.crt/tls.key por un certificado de vuestra CA y usar un nombre DNS incluido en ese certificado. Las credenciales del panel se envían por HTTPS.

Los permisos de pfREST deben permitir GET /api/v2/firewall/rules, GET /api/v2/firewall/rule, PATCH /api/v2/firewall/rule y GET/POST /api/v2/firewall/apply. Las claves heredan los privilegios del usuario que las genera. Restringe el acceso de la API al servidor 192.168.30.174 en sus listas de acceso. La lectura validada previamente con tu clave no comprueba los permisos de escritura. Una clave admin tiene acceso amplio, conviene asignar estos endpoints a un usuario dedicado antes del uso por profesorado.

## Prueba real

Entra al panel, comprueba la tarjeta del Aula 9 y pulsa Bloquear Internet. El backend localiza la regla por tracker, valida origen/destino/tipo/interfaz, consulta de nuevo su índice y cambia únicamente disabled. Aplica el filtro de forma síncrona y comprueba el estado aplicado y la regla. Comprueba una conexión NUEVA desde un PC del Aula 9 y el acceso SMB al servidor. Pulsa Permitir Internet y verifica la restauración. Comprueba también que otro PC fuera del alias sigue saliendo a Internet.

Esta versión controla la regla IPv4. Las conexiones existentes pueden continuar hasta que caduquen o se eliminen sus estados. No elimina estados automáticamente. Los permisos IPv6 dependen de vuestra política de red. El estado mostrado es el de la regla y de la aplicación del filtro, no una prueba de conectividad de cada PC. Verifica que Sare_pribatuak contiene todos los destinos internos necesarios.

Si hay cambios pendientes en pfSense, el panel pide revisarlos desde su interfaz antes de realizar otra escritura, ya que Apply afecta a las modificaciones pendientes del firewall. Si una llamada falla tras guardar, muestra Sin confirmar. Revisa la regla y Apply Changes en pfSense antes de repetir.

Evita reordenar o editar reglas desde pfSense durante un cambio desde el panel. Los índices de la API son posicionales. El panel relee el ID y el tracker justo antes de escribir, pero pfREST no proporciona aquí una operación atómica por tracker. Un único worker serializa las operaciones del panel.

## Añadir aulas

Crea el alias y su regla de bloqueo en pfSense, prueba su posición y comportamiento y anota el tracker devuelto por la API. En config/settings.json, edita la entrada correspondiente, por ejemplo:

```json
{"id": 10, "name": "Aula 10", "tracker": "TRACKER_REAL", "source": "ALIAS_REAL"}
```

El panel solo admite reglas IPv4 de bloqueo/rechazo en LAN y destino !Sare_pribatuak. Reinicia con docker compose restart. No crea ni reordena reglas. No deduzcas trackers a partir del número de aula.

## Mantenimiento

```bash
docker compose logs --tail=100
docker compose restart
docker compose down
```

Conserva una copia privada de config junto con el proyecto. Contiene la clave API, el hash de contraseña, la clave de sesión y el certificado/clave TLS. Para cambiar la clave API edita config/api-key y reinicia. Tras actualizar pfSense, reinstala pfREST para la versión correspondiente y prueba lectura, bloqueo y restauración. El proyecto pfREST está en mantenimiento. El conector está concentrado en app.py para facilitar una migración posterior.

## Idiomas

La interfaz de acceso y el panel incluyen selector ES / EU. La preferencia se recuerda durante un año en una cookie y se conserva al cerrar sesión. Sin selección previa, se utiliza el idioma compatible del navegador o castellano. Los textos se centralizan en translations.py. Los alias, trackers y nombres técnicos de las reglas no se traducen.

Para actualizar una instalación existente, sustituye los archivos del código y ejecuta `docker compose up -d --build`. Conserva `config/` y no vuelvas a ejecutar el asistente.
