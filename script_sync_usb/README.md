---
tipo: readme
estado: activo
---
# script_sync_usb/ — sincronización bidireccional de la carpeta SGDP por un USB compartido, con papelera y detección de conflictos
<!-- suite:inicio -->
**Suite `sync_usb`** · objetivo *sistema* · estado *activo* · python · interfaz cli

Sincroniza en ambas direcciones una carpeta local con su copia en un USB compartido (dos equipos, un USB que va y viene), con papelera y detección de conflictos; solo biblioteca estándar de Python.

- Escribe en: archivos · simula por defecto: no
- Depende de: python3
- Nota: Fija la carpeta SGDP en el USB y aplica la convención de nombres del SGDP: los PDF gemelos de nombre antiguo pasan a la papelera (.sgdp-papelera).

Comandos:

```bash
main.py --local <carpeta> --usb <montaje> [--dry-run]
sincronizar_usb.sh --local <carpeta> --usb <montaje> [--dry-run]
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Sincroniza en ambas direcciones la carpeta local `SGDP` de un equipo con su copia en un USB que va y viene entre
dos equipos. No es una herramienta genérica de carpetas: está atada a la carpeta `SGDP` y a la convención de
nombres del archivo documental del SGDP.

- **Cómo decide:** un archivo que está en un solo lado se copia al otro; si está en los dos y el contenido (tamaño y
  SHA-256) es igual, se omite; si difiere, gana el de fecha de modificación más reciente. Si las dos fechas distan
  3 segundos o menos (`TOLERANCIA_MTIME`; FAT redondea a 2 s), no elige: copia cada versión al otro lado como
  `nombre (conflicto LAPTOP <hash>).ext` y `nombre (conflicto USB <hash>).ext` y avisa. La copia de conflicto lleva
  un hash del contenido, así que repetir la corrida no la duplica.
- **Qué escribe:** las copias en el otro lado (con `shutil.copy2`, que conserva la fecha) y, antes de sobrescribir un
  archivo, lo mueve a `.sgdp-papelera/<AAAAMMDD-HHMMSS>/` en la raíz de su lado. Crea la carpeta del USB si no existe.
- **Qué mueve sin que se lo pidan:** antes de comparar, en cada lado busca PDF gemelos en una misma carpeta (mismo
  SHA-256) en los que uno sigue la convención de nombres vigente del SGDP (empieza por un prefijo de serie como
  `OF-`, `MEM-`, `INF-`…) y otro no; el de nombre antiguo se mueve a la papelera `.sgdp-papelera`. Un PDF sin gemelo exacto no
  se toca.
- **Qué no hace:** no propaga borrados (lo que falta en un lado se vuelve a copiar desde el otro; borrar exige
  hacerlo a mano en los dos), no resuelve conflictos, no sincroniza archivos ni carpetas ocultos (los que empiezan
  por `.`) ni sus propios archivos internos.
- **Simulación:** no simula por defecto; `--dry-run` muestra el plan sin escribir ni mover nada. Sin `--dry-run` ni
  `--si`, antes de aplicar hace una pasada en seco, muestra las cifras y pide confirmación.

## Uso

```bash
./sincronizar_usb.sh --dry-run                       # autodetecta USB y carpeta local; simula
./sincronizar_usb.sh                                 # aplica, tras confirmar
python3 main.py --local "$HOME/Documentos/SGDP" --usb "/media/<usuario>/<USB>" --dry-run
```

Pide una clave de autorización antes de hacer nada, también con `--dry-run`. La clave esperada no está en el
código: se lee de `~/.config/scripts_for_linux/sgdp_usb_clave` (nombre histórico del repo: la clave no se mueve) (una línea, `chmod 600`) o de la variable
`SGDP_USB_CLAVE_ESPERADA`; sin ninguna de las dos, el script se niega y dice dónde escribirla. La que se da en
cada uso llega por `--clave` o por `SGDP_USB_CLAVE` (uso no interactivo).

| opción | qué hace | por defecto |
|---|---|---|
| `--local RUTA` | carpeta local | la primera que exista de «~/Documentos/SGDP», «~/Documents/SGDP», «~/SGDP» |
| `--usb RUTA` | carpeta o unidad del USB | autodetectada (ver abajo) |
| `--dry-run` | simula | no |
| `--si` | aplica sin pedir confirmación | no |
| `--clave CLAVE` | clave de autorización | se pregunta (o `SGDP_USB_CLAVE`) |
| `-h`, `--help` | ayuda | — |

**La carpeta del USB.** Si `--usb` (o la unidad detectada) no se llama `SGDP` ni contiene una subcarpeta `Oficios`,
la herramienta usa `<ruta>/SGDP`: con `--usb /media/<usuario>/<USB>` sincroniza `/media/<usuario>/<USB>/SGDP`. La
autodetección busca carpetas escribibles en `/media/$USER`, `/run/media/$USER`, `/media` y `/mnt` (Linux), en
`/Volumes` salvo el disco del sistema (macOS) o unidades extraíbles (Windows); si hay varias, pregunta cuál.

Códigos de salida: 0 hecho o cancelado · 1 clave incorrecta, carpeta no encontrada o local igual al USB · 2 opción
desconocida.

Requisitos: Python 3, solo biblioteca estándar.

## Estructura

| archivo | qué hace |
|---|---|
| `main.py` | todo: configuración al inicio (clave, nombre de carpeta, papelera, tolerancia), detección de USB y carpeta local, retiro de PDF de nombre antiguo, plan y copia, interfaz |
| `sincronizar_usb.sh` | lanzador para Linux y macOS: `exec python3 main.py "$@"` |
| `sincronizar_usb.bat` | lanzador para Windows; hoy roto (ver Límite honesto) |

## Límite honesto

- **El lanzador de Windows no funciona**: `sincronizar_usb.bat` llama a `sincronizar_usb.py`, que no existe (el
  archivo es `main.py`). En Windows hay que ejecutar `python main.py` desde la carpeta (ver `estado.md`
  §Por hacer).
- **La clave vive fuera del repo** (`~/.config/scripts_for_linux/sgdp_usb_clave` (nombre histórico del repo: la clave no se mueve)); cambiarla es editar ese archivo
  en cada máquina que sincroniza. La anterior estuvo publicada y debe darse por expuesta (`docs/decisiones.md`).
- **Atada al SGDP**: el nombre `SGDP`, la papelera `.sgdp-papelera`, la excepción `Oficios` y el patrón de nombres
  vigentes viven en `main.py`. Para otra carpeta habría que editarlos.
- **El retiro de PDF de nombre antiguo mueve archivos del usuario** en los dos lados, en cada corrida; en `--dry-run`
  el aviso «apartada(s)» se imprime aunque no se mueva nada.
- **Gana el más nuevo por fecha**: si el reloj de un equipo está mal, la versión equivocada sobrescribe a la buena;
  la buena queda en la papelera `.sgdp-papelera`, que nunca se vacía sola.
- **Los conflictos se resuelven a mano**: abrir la pareja `(conflicto …)` y borrar la que sobra en los dos lados.
- **Un archivo borrado reaparece**: como los borrados no se propagan, lo eliminado en un solo lado vuelve en la
  siguiente corrida.
- **No sigue el patrón `main` + `config` + `lib`** del repositorio: es un solo archivo con sus lanzadores.
- Retirar el USB solo después del resumen final y con «expulsar» del sistema.
