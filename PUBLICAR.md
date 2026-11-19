# Publicar en GitHub

## Opción gráfica con Visual Studio Code

1. Extrae el paquete y abre la carpeta `ceinpro-aulas` con **Archivo → Abrir carpeta**.
2. En **Control de código fuente**, pulsa **Inicializar repositorio** si todavía no está inicializado.
3. Revisa los cambios: deben aparecer los archivos del código y la documentación, pero no `config/`, claves privadas ni archivos `.env`.
4. Escribe `Panel inicial de control de Internet por aula` y crea el primer commit. Si pide preparar los archivos, acepta después de revisar la lista.
5. Pulsa **Publicar rama / Publish Branch**, inicia sesión en GitHub si lo solicita y elige un repositorio privado llamado `pfSenseAulas`.

Para alojarlo en la organización CEINPRO, crea primero un repositorio vacío desde GitHub seleccionando la organización como propietaria. No añadas README, licencia ni .gitignore en GitHub, porque ya hay archivos locales. En VS Code usa **Git: Add Remote**, nombre `origin`, URL HTTPS del repositorio creado; después **Git: Push**. Necesitas permisos para crear repositorios en la organización.

## Opción terminal

Desde la carpeta del proyecto, si todavía no tiene repositorio Git:

```bash
git init -b main
git add .
git diff --cached --name-only
```

Revisa esa lista antes de continuar. No debe contener la carpeta `config/` ni credenciales. Después:

```bash
git commit -m "Panel inicial de control de Internet por aula"
```

Crea en GitHub un repositorio privado vacío y copia su URL. Para un repositorio de la organización llamado `pfSenseAulas`:

```bash
git remote add origin https://github.com/ceinpro/pfSenseAulas.git
git push -u origin main
```

Si Git solicita la identidad para el commit, configura tu nombre y correo institucional con `git config user.name` y `git config user.email` dentro de este repositorio. La autenticación HTTPS de GitHub se realiza con un gestor de credenciales o un token, no con la contraseña de la cuenta.

## Instalación ya existente

Puedes añadir estos archivos de documentación y `.gitignore` a la carpeta de tu instalación y seguir el mismo proceso. Conserva `config/` en el servidor. Un `.gitignore` no deja de seguir archivos que ya estuvieran versionados: si Git muestra archivos de `config/` como seguidos, retíralos del índice con `git rm -r --cached config` antes de hacer el commit. Esto mantiene los archivos locales.

Si una clave ya se hubiera publicado en un commit, hay que revocarla y sustituirla; borrarla en un commit posterior no la elimina del historial.

Subir este repositorio guarda el código. No publica el panel en Internet ni despliega automáticamente el contenedor.
