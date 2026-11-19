# Cambios

## 1.1.0

- Nombre del centro configurable en `config/settings.json` y visible en acceso y panel.
- Instalador genérico: URL de pfSense, certificado, red de publicación, cantidad de aulas y criterios de reglas configurables; aulas inicialmente sin vincular.
- Interfaz y destino de las reglas configurables por centro y por aula, manteniendo la validación de reglas IPv4.
- Nombres opcionales de aula en euskera con `name_eu`.
- IP y puerto de Docker en `.env`, con escucha local predeterminada.
- Manual de instalación y actualización desde GitHub, migración desde ZIP y ejemplos genéricos.
- Configuraciones anteriores conservan sus aulas, secretos y criterios de reglas si no se han personalizado los nuevos campos.

## 1.0.0 — 2026-11-19

- Selector de idioma ES / EU con botones de alto contraste en acceso y cabecera.
- Versión visible junto al título, también en pantallas pequeñas.
- Versión centralizada en VERSION y recursos CSS/JS identificados por versión.
- Licencia GNU GPL versión 3 y documentación de actualización.
- Interfaz y mensajes del panel en castellano y euskera.
