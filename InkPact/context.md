# Contexto para la página web de Inkpact

Este documento tiene todo lo necesario para crear la página de descarga de **Inkpact**, a mano o pasándoselo a una IA o a un generador de webs. Los datos `<ENTRE_ÁNGULOS>` hay que rellenarlos.

---

## 1. Qué es Inkpact

**Inkpact** es una **pizarra overlay para coaches de esports** en Windows. Sirve para dibujar encima de cualquier cosa en pantalla (el juego, una repetición, un vídeo de YouTube o Discord) mientras se explica una jugada. Es parecida a EpicPen o ZoomIt, pero está pensada para tácticas de equipo.

- **Gratis y de código abierto** (licencia MIT).
- **Portable:** no se instala. Se descomprime y se ejecuta, y cabe en un USB.
- **Ligera:** unos 2-3 MB de descarga. No consume recursos mientras no se usa.
- **Idiomas:** español (por defecto) e inglés.
- **Público:** coaches, analistas, capitanes de equipo, creadores de contenido y streamers de Valorant, Overwatch 2 y League of Legends, o de cualquier otro juego.

**Frase corta (eslogan), elige una:**
- "Dibuja la jugada encima del juego."
- "La pizarra táctica que flota sobre tu pantalla."
- "Explica la estrategia sin pausar nada."

**Descripción de un párrafo:**
> Inkpact es una pizarra transparente que flota sobre tu pantalla. Dibuja flechas, zonas y rutas encima del juego, de una repetición o de Discord sin pausar nada. Coloca a los agentes, héroes o campeones de cada equipo para armar composiciones, marca zonas de humo o visión, congela la pantalla para explicar con calma y guarda tus jugadas por páginas. Es gratis, de código abierto y portable: descomprime y úsala.

---

## 2. Funciones principales (para la sección "Características")

| Función | Texto para la web |
|---|---|
| Overlay con click-through | Dibuja encima de cualquier app. Con un atajo vuelves a usar el juego sin cerrar la pizarra. |
| Herramientas de dibujo | Lápiz, resaltador, línea, flecha, rectángulo, elipse, texto (con tamaño de letra) y borrador. |
| Puntero láser | Mantén el clic para señalar. Deja una estela que desaparece sola. |
| Zonas semitransparentes | Círculos, conos de visión, anillos, polígonos y bandas para marcar humos, rangos o áreas. Se pueden guardar como presets. |
| Banco de personajes | Valorant, Overwatch 2 y LoL, filtrados por rol y con buscador. Se arrastran al tablero con marco azul (aliado) o rojo (enemigo). |
| Composiciones | Plantillas de 5 huecos por equipo. Cambiar de personaje, marcarlo como caído y ponerle etiquetas ("Jugador 1"). |
| LoL: wards y hechizos | Wards como fichas en el mapa. Hechizos de invocador (Destello, Teleportar, Prender…) pegados al campeón. |
| Congelar pantalla | Congela lo que se ve para explicar algo que no se puede pausar. |
| Mapas de fondo | Pon un mapa táctico de fondo o suelta cualquier imagen. |
| Páginas | Una jugada por página, como diapositivas. |
| Guardar y compartir | Archivos `.inkpact` autocontenidos. Exportar PNG o copiar la imagen para pegarla en Discord. |
| Atajos globales | Todos se pueden configurar. Por ejemplo, `Ctrl+Shift+D` activa o desactiva el dibujo desde cualquier app. |
| Barra flexible | Barra vertical u horizontal que se oculta al compartir pantalla: tú la ves y tu audiencia no. |
| Privacidad | Sin cuentas, sin anuncios y sin telemetría. Solo descarga los retratos de personajes de las fuentes públicas de cada juego. |

---

## 3. Descarga (lo más importante de la página)

El **botón principal** tiene que ser grande y visible arriba del todo:

> **⬇ Descargar Inkpact para Windows** (portable, gratis)
> Windows 10/11 · 64 bits · ~2,5 MB

### Enlaces

- **Repositorio:** `<URL_DEL_REPO>` (ej. `https://github.com/<usuario>/inkpact`)
- **Última versión (siempre actualizada):** `<URL_DEL_REPO>/releases/latest`
- **Descarga directa del portable:** `<URL_DEL_REPO>/releases/latest/download/Inkpact-<VERSIÓN>-portable.zip`
- **Instalador (alternativa):** `<URL_DEL_REPO>/releases/latest/download/Inkpact_<VERSIÓN>_x64-setup.exe`
- **Sumas de verificación:** `<URL_DEL_REPO>/releases/latest/download/SHA256SUMS.txt`

> **Nota técnica:** el nombre del archivo lleva la versión (`Inkpact-1.0.0-portable.zip`). Hay dos opciones para que la página no quede desactualizada:
> 1. **La más simple:** el botón enlaza a `<URL_DEL_REPO>/releases/latest` y el usuario elige el archivo allí.
> 2. **La mejor:** leer la última versión con la API pública de GitHub (sin clave) y construir el enlace directo:
>    ```js
>    const r = await fetch('https://api.github.com/repos/<usuario>/<repo>/releases/latest');
>    const rel = await r.json();
>    const zip = rel.assets.find(a => a.name.endsWith('-portable.zip'));
>    // zip.browser_download_url, rel.tag_name (versión), zip.size
>    ```
>    Si la API falla, el botón debe seguir funcionando con el enlace de la opción 1.

### Cómo se instala (3 pasos para la web)

1. Descarga el `.zip` y descomprímelo donde quieras (Escritorio, USB…).
2. Abre `Inkpact.exe`.
3. Pulsa `Ctrl+Shift+D` para dibujar y otra vez para volver al juego.

### Requisitos

- Windows 10 o 11 (64 bits).
- WebView2, que ya viene en Windows 11 y casi todos los Windows 10. Si falta: https://go.microsoft.com/fwlink/p/?LinkId=2124703
- El juego debe estar en **ventana sin bordes** (borderless), no en pantalla completa exclusiva.

---

## 4. Seguridad y confianza (sección obligatoria)

Es una app que se descarga y se ejecuta, así que la página tiene que dar confianza:

- **Descarga solo desde esta página o desde GitHub.** Son las únicas copias oficiales.
- **Código abierto:** cualquiera puede revisar el código en `<URL_DEL_REPO>`.
- **Compilado por GitHub:** los archivos se generan automáticamente en GitHub Actions a partir del código público, no en el PC de nadie. Incluyen una atestación de procedencia verificable.
- **Verifica tu descarga** (opcional, para usuarios avanzados):
  ```powershell
  Get-FileHash .\Inkpact-<VERSIÓN>-portable.zip -Algorithm SHA256
  ```
  El resultado debe coincidir con el de `SHA256SUMS.txt`.
- **Aviso de Windows SmartScreen:** como el ejecutable aún no tiene firma digital de pago, Windows puede mostrar "Windows protegió tu PC". Se abre con *Más información → Ejecutar de todas formas*. Conviene explicarlo con una captura para que nadie se asuste.
- **Inkpact es gratis.** Si alguien te lo vende o te pide desactivar el antivirus, no es la copia oficial.

---

## 5. Donaciones (las gestiona `<NOMBRE_DEL_AMIGO>`)

- **Plataforma:** `<Ko-fi / Buy Me a Coffee / PayPal / Patreon>`
- **Enlace:** `<URL_DE_DONACIÓN>`
- **Tono:** opcional y sin presión. La app es y seguirá siendo gratis.

**Texto sugerido:**
> **¿Te ayuda Inkpact con tu equipo?** Es gratis y lo seguirá siendo. Si quieres apoyar su desarrollo (nuevos juegos, mapas, la pizarra compartida con tus jugadores), puedes invitarnos un café. ☕
> [ Invítanos un café ]

**Importante:**
- El mismo enlace de donación debe ponerse en GitHub (Settings → Secrets and variables → Actions → Variables → `INKPACT_DONATE_URL`). Así aparece también dentro de la app, en Ajustes → Acerca de.
- No poner la donación como paso antes de descargar ni como ventana emergente. Debe ser una sección propia o un botón secundario.

---

## 6. Estructura de la página sugerida

1. **Cabecera:** logo + "Inkpact" + enlace a GitHub + selector ES/EN.
2. **Hero:** eslogan, descripción corta, **botón grande de descarga**, debajo "Windows 10/11 · Gratis · Código abierto · v`<VERSIÓN>`" y una captura o GIF de la app dibujando sobre un juego.
3. **Cómo funciona:** los 3 pasos (descargar, abrir, `Ctrl+Shift+D`).
4. **Características:** tarjetas con las funciones de la sección 2 (6-8 tarjetas con icono).
5. **Demo:** GIF o vídeo corto (10-20 s) dibujando una jugada sobre un mapa.
6. **Juegos compatibles:** "Valorant · Overwatch 2 · League of Legends · y cualquier juego con imágenes propias". Solo texto: **no usar logos oficiales** (ver sección 8).
7. **Seguridad:** sección 4, resumida.
8. **Apoya el proyecto:** sección 5.
9. **Preguntas frecuentes:** sección 7.
10. **Pie:** licencia MIT, enlace a GitHub, aviso legal (sección 8) y "Reportar un error" (`<URL_DEL_REPO>/issues`).

**Diseño:**
- **Fondo:** oscuro, como la app (`#14161D`, tarjetas `#222530`).
- **Texto:** `#E9ECF2`, secundario `#8C93A3`.
- **Acento:** celeste `#64D2FF` (botones, enlaces).
- **Colores de equipo para detalles:** azul aliado `#0A84FF` y rojo enemigo `#FF3B30`.
- **Fuente:** sans-serif moderna (Inter, Segoe UI o similar).
- **Estilo:** limpio y "gamer" sin exagerar. Bordes redondeados (14 px), mucho espacio y capturas grandes.
- **Logo/icono:** en el repositorio, `apps/desktop/src-tauri/icons/` (`128x128@2x.png`, `Square310x310Logo.png`, `icon.ico`).
- **Rendimiento:** página estática y ligera, que cargue rápido en móvil. Se puede alojar gratis en **GitHub Pages**, Netlify o Cloudflare Pages.

**Capturas que hacen falta** (hacerlas con la app real):
- Dibujo de una jugada sobre un mapa de Valorant u Overwatch, con flechas y zonas.
- Banco de personajes abierto con una composición de 5 vs 5 en el tablero.
- Campeón de LoL con hechizos pegados y wards en el mapa.
- Barra de herramientas (vertical y horizontal).
- GIF del puntero láser.

> Para hacer capturas que incluyan la barra, abre la app con la variable `INKPACT_CAPTURE_TOOLBAR=1`. Por defecto se oculta al capturar.

---

## 7. Preguntas frecuentes

**¿Es gratis?** Sí, totalmente. Sin anuncios, sin cuentas y sin versión de pago.

**¿Es seguro? Windows me muestra un aviso.** Sí. El aviso de SmartScreen aparece con programas nuevos sin firma de pago. El código es público y los archivos se compilan en GitHub. Pulsa *Más información → Ejecutar de todas formas*.

**¿Necesito instalar algo?** No. Descomprime y abre `Inkpact.exe`. Todo se guarda en la carpeta `data` de al lado. Para borrarla, borras la carpeta.

**¿Me pueden banear por usarla?** Inkpact no lee ni modifica la memoria del juego: es una ventana transparente encima, como Discord o OBS. Aun así, úsala para coaching y análisis, no en partidas competitivas en curso. *(Texto orientativo: no es asesoría legal ni garantía de las desarrolladoras de los juegos.)*

**No veo la pizarra sobre el juego.** Pon el juego en "ventana sin bordes" (borderless). La pantalla completa exclusiva no permite overlays.

**En Discord u OBS no se ven mis dibujos.** Comparte la **pantalla completa**, no solo la ventana del juego.

**¿Funciona con otros juegos?** Sí: el dibujo funciona sobre cualquier cosa. El banco trae Valorant, Overwatch 2 y LoL, y puedes añadir personajes propios poniendo imágenes en una carpeta.

**¿Mac o Linux?** De momento solo Windows 10/11.

**¿Cómo apoyo el proyecto?** Con una donación (sección "Apoya el proyecto"), reportando errores en GitHub o compartiéndola con tu equipo.

---

## 8. Aviso legal (obligatorio en el pie)

> Inkpact no está afiliado, asociado ni respaldado por Riot Games, Blizzard Entertainment ni ninguna otra desarrolladora. Valorant y League of Legends son marcas de Riot Games, Inc. Overwatch es una marca de Blizzard Entertainment, Inc. Las imágenes de personajes que la aplicación muestra se descargan de fuentes públicas y pertenecen a sus propietarios.

**Reglas para la web:**
- **No usar** logos oficiales de los juegos, arte oficial ni retratos de personajes como decoración principal de la página.
- En las capturas de la app pueden verse retratos (es uso dentro de la herramienta), pero no deben ser el reclamo principal.
- No usar "Valorant", "Overwatch" ni "League of Legends" en el nombre del dominio.
- Si se usan analíticas o cookies en la web, poner un aviso de cookies y preferir analíticas sin cookies (Plausible, Umami, Cloudflare Web Analytics).

---

## 9. Textos en inglés (para la versión EN)

- **Tagline:** "Draw the play right on top of the game."
- **Short description:** "Inkpact is a transparent whiteboard that floats over your screen. Draw arrows, zones and routes over your game, a replay or Discord without pausing anything. Place agents, heroes or champions to build team comps, mark smokes and vision, freeze the screen to explain calmly, and save your plays as pages. Free, open source and portable: just unzip and run."
- **Button:** "Download for Windows (portable, free)"
- **Donation:** "Does Inkpact help your team? It's free and always will be. If you'd like to support development, buy us a coffee. ☕"

---

## 10. Datos rápidos

| Dato | Valor |
|---|---|
| Nombre | Inkpact |
| Versión actual | `<VERSIÓN>` (en el repo: `apps/desktop/src-tauri/tauri.conf.json`) |
| Plataforma | Windows 10/11, 64 bits |
| Tamaño | ~2,5 MB (portable .zip) |
| Licencia | MIT (código abierto) |
| Precio | Gratis |
| Tecnología | Tauri 2 (Rust) + TypeScript |
| Repositorio | `<URL_DEL_REPO>` |
| Donaciones | `<URL_DE_DONACIÓN>` (gestiona `<NOMBRE_DEL_AMIGO>`) |
| Reportar errores | `<URL_DEL_REPO>/issues` |
| Vulnerabilidades | En privado: `<URL_DEL_REPO>/security` |
