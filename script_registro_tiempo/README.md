---
tipo: readme
estado: activo
---
# script_registro_tiempo/ — el tiempo de lectura, pantalla y trabajo, en el vault y en Super Productivity

<!-- suite:inicio -->
**Suite `registro_tiempo`** · objetivo *personal* · estado *borrador* · python · interfaz cli

Reúne el tiempo de KOReader, Zotero, ActivityWatch y Super Productivity en el vault y lo lleva a Super Productivity.

- Escribe en: vault, archivos, sistema · simula por defecto: sí
- Entrada: tareas/registro-tiempo.yml (categorías, metas y estructura propuesta)
- Depende de: python3 (con PyYAML), core/env.py, core/py-common/logger.py, Super Productivity 18 con la API REST local activada (opcional), ActivityWatch o awatcher (opcional)
- Timer: `registro-tiempo.timer`
- Nota: El plugin de plugin-sp/ se sube a mano en Super Productivity (Ajustes → Plugins); la suite solo lo empaqueta.

Comandos:

```bash
main.py recoger
main.py recoger --aplicar
main.py planificar <plan.txt> --aplicar
main.py plugin --aplicar
main.py timer --aplicar
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-25); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Una pasada (`recoger`) lee cuatro fuentes y deja el tiempo de cada día donde se respalda y se revisa:

| fuente | qué aporta | cómo se lee |
|---|---|---|
| KOReader (`KOREADER_STATS`) | minutos por día y por libro | `page_stat_data`, solo lectura |
| Zotero (`ZOTERO_DB`) | minutos por obra | el acumulado de Ethereal Style, por diferencia entre pasadas |
| ActivityWatch (`localhost:5600`) | programas, sitios y categorías | cubos de ventanas, ausencia y web; opcional |
| Super Productivity (`tareas/sync-data.json`) | tiempo por proyecto y etiqueta, tareas hechas | el archivo de su sincronización local, solo lectura |

Escribe tres cosas: el **historial** por mes (`tareas/registro/datos/AAAA-MM.json`), la **nota semanal**
(`tareas/registro/AAAA-MM-DD-semana.md`, generada, para la revisión semanal en Obsidian) y, si Super Productivity
está abierto, la **tarea portadora** que su plugin convierte en tiempo por día dentro del proyecto «Registro
automático». `planificar` hace el camino inverso: un plan en sintaxis corta (del vault o del skill
`productividad-personal`) se vuelve tareas de Super Productivity sin copiar y pegar.

## Uso

```bash
python3 main.py recoger                       # simula: lo que mediría hoy y los seis días anteriores
python3 main.py recoger --aplicar             # escribe historial, nota semanal y entrega a SP
python3 main.py recoger --dias 30 --aplicar   # recalcula un mes (KOReader, ActivityWatch y SP se recalculan; Zotero no)
python3 main.py planificar plan.txt           # simula: qué tareas crearía y con qué campos
python3 main.py planificar plan.txt --aplicar # las crea por la API REST (SP abierto)
python3 main.py plugin --aplicar              # empaqueta plugin-sp/ en ~/.local/state/registro-tiempo/registro-tiempo-sp.zip
python3 main.py timer --aplicar               # instala y activa registro-tiempo.timer (cada hora)
```

Puesta en marcha, una sola vez:

1. En Super Productivity: Ajustes → Sync → archivo local apuntando a `~/Documents/tareas` (la carpeta, no el
   archivo), y Ajustes → Misceláneo → «Local REST API» activada.
2. `python3 main.py plugin --aplicar` y subir el `.zip` en Ajustes → Plugins.
3. Copiar el ejemplo de abajo a `~/Documents/tareas/registro-tiempo.yml` (ya hay uno con la estructura propuesta).
4. Para medir pantalla en KDE con Wayland, instalar ActivityWatch con el observador `awatcher` y, para sitios, la
   extensión aw-watcher-web del navegador. Sin ellos la suite mide lo demás y lo dice en la nota.
5. `python3 main.py timer --aplicar`.

`tareas/registro-tiempo.yml` (forma; el vigente es el del vault):

```yaml
fuentes_a_sp:                 # qué tarea de «Registro automático» recibe cada fuente
  koreader: Lectura en KOReader
  zotero: Lectura en Zotero
categorias:                   # gana la primera que coincide; a_sp: true la lleva a SP; vigilar: true va al resumen
  redes: {dominios: [facebook.com, instagram.com, tiktok.com, x.com], titulos: [Facebook, Instagram, TikTok],
          a_sp: true, tarea_sp: Redes sociales, vigilar: true}
  estudio: {dominios: [duolingo.com, edx.org], apps: [rstudio, positron, xournalpp]}
metas_semanales_horas:        # por proyecto de SP; la nota semanal muestra el avance
  Tesis: 6
estructura_sp:                # lo que el panel del plugin propone y aplica tras mostrarlo
  proyectos: [{titulo: Tesis}]
  etiquetas: [{titulo: lectura}]
  archivar: [Bloomberg]
```

## Estructura

`main.py` (orquestación) · `config.py` (rutas relativas, puertos, umbrales) · `lib/`: `entorno.py` (rutas por
`core/env.py`), `koreader.py`, `zotero.py`, `activitywatch.py`, `superproductivity.py` (fuentes), `clasificar.py`
(categorías), `recoger.py` (una pasada), `registro.py` (historial y datos para SP), `informe.py` (nota semanal),
`plan.py` (sintaxis corta → campos), `sp_rest.py` (API REST de SP), `instalar.py` (zip y timer), `validator.py`,
`cli.py`, `logger.py` · `plugin-sp/` (el plugin: `manifest.json`, `plugin.js`, `index.html`, `icon.svg`) ·
`systemd/` (plantillas del servicio y el timer).

## Límite honesto

- **Zotero se mide por diferencia**: la primera pasada fija la línea base y no inventa tiempo; lo leído entre dos
  pasadas se atribuye al día de la segunda. Si se pierde el historial de un día de Zotero, no vuelve.
- **El tiempo de fuera no se cronometra en SP**: si lees en KOReader con el temporizador de SP corriendo, ese tiempo
  cuenta dos veces. Por eso va a su propio proyecto y la nota semanal separa «trabajo registrado en SP».
- **Sin ActivityWatch no hay tiempo de pantalla**: Zen borra su historial al cerrar y Firefox no guarda duraciones.
- **La API REST no crea etiquetas ni proyectos**: `planificar` avisa y omite lo que no existe; los crea el plugin
  desde `estructura_sp`.
- **En Super Productivity 18.10 un plugin subido a mano no puede ejecutar Node** (solo los incluidos): por eso los
  datos llegan por la API REST y no por archivo.
- `sync-data.json` cifrado no se lee: la suite lo informa y sigue con las demás fuentes.
