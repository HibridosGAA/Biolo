# Biología NM en Render (con contraseña)

## 1. Subir a GitHub
1. Crea un repositorio **privado** en GitHub (recomendado: las preguntas son material con licencia CC BY-NC-ND).
2. Sube TODO el contenido de esta carpeta (server.js, login.html, package.json, render.yaml, public/, etc.).
   - Con Git: `git init`, `git add .`, `git commit -m "Biología NM"`, `git branch -M main`, `git remote add origin URL_DE_TU_REPO`, `git push -u origin main`
   - O desde la web de GitHub: "Add file → Upload files" (arrastra la carpeta public completa).

## 2. Crear el servicio en Render
1. En render.com: **New → Web Service** y conecta tu repositorio de GitHub.
2. Configura: Runtime **Node**, Build Command `echo ok`, Start Command `node server.js`.
   (O usa **New → Blueprint**, que lee render.yaml automáticamente.)
3. En **Environment** agrega:
   - `APP_PASSWORD` = la contraseña que tú elijas
   - `SESSION_SECRET` = una frase larga y aleatoria (así tu sesión sobrevive a reinicios)
4. Deploy. Render te dará una URL tipo https://biologia-nm.onrender.com

## Cómo funciona la sesión
- Al ingresar la contraseña se guarda una cookie válida por 1 año, que se renueva cada vez que entras: no se cierra sola.
- Solo se cierra si pulsas "Cerrar sesión" (arriba a la derecha), borras las cookies o cambias APP_PASSWORD / SESSION_SECRET.
- Tu progreso y el modo claro/oscuro se guardan en el navegador de cada dispositivo.
- Sin contraseña no se puede ver ninguna página, ni siquiera las imágenes de las preguntas.

## Notas
- En el plan gratuito de Render la web "duerme" tras un rato sin visitas y tarda ~30-60 s en despertar. La sesión no se pierde.
- Para cambiar la contraseña: edita APP_PASSWORD en Render y guarda (se cerrará la sesión en todos los dispositivos).
- Prueba local: `APP_PASSWORD=miclave node server.js` y abre http://localhost:3000
