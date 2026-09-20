---
tipo: readme
estado: activo
---
# script_sync_usb/ — sincronización bidireccional de una carpeta por un USB compartido, con papelera y detección de conflictos
<!-- suite:inicio -->
**Suite `sync_usb`** · objetivo *sistema* · estado *activo* · python · interfaz cli

Sincroniza en ambas direcciones una carpeta local con su copia en un USB compartido (dos equipos, un USB que va y viene), con papelera y detección de conflictos; solo biblioteca estándar de Python.

- Escribe en: archivos · simula por defecto: no
- Depende de: python3
- Nota: Antes 05_sgdp/sincronizacion_usb (M10 D2, 2026-09-15). Caso de uso original: el archivo documental del SGDP entre las laptops de las secretarías.

Comandos:

```bash
main.py --local <carpeta> --usb <montaje> [--dry-run]
sincronizar_usb.sh --local <carpeta> --usb <montaje> [--dry-run]
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-09-20); no se edita a mano.</sub>
<!-- suite:fin -->

> Suite genérica de `scripts_for_linux` desde 2026-09-15 (M10 D2; antes `05_sgdp/sincronizacion_usb`): sirve para cualquier carpeta que viaje en un USB entre dos equipos (el caso de origen es el archivo documental del SGDP). Invocación: `main.py --local <carpeta> --usb <montaje>` o `sincronizar_usb.sh`/`.bat`.

Herramienta **nativa** para compartir los documentos del SGDP entre las
laptops de las secretarías usando un **USB que va y viene**, en **ambas
direcciones**:

```
Laptop Secretaria 1  <->  USB compartido  <->  Laptop Secretaria 2
```

## ¿Por qué una herramienta aparte y no el navegador?

El botón **«Sincronizar»** de la plataforma solo copia **del servidor a una
carpeta de la laptop**, en **una sola dirección**, y el navegador **no puede
detectar el USB** al conectarlo (es una limitación de seguridad del navegador,
no del sistema). Para copiar **laptop ↔ USB ↔ laptop** hace falta un programa
nativo. Este lo es.

Flujo recomendado: la plataforma baja los documentos del servidor a tu carpeta
local `SGDP` (botón «Sincronizar» de la web); **esta** herramienta refleja esa
carpeta `SGDP` con el USB en las dos direcciones.

## Lo primero: nunca se pierde nada

- **No borra nada.** Si un archivo falta en un lado, se vuelve a copiar del
  otro; **una supresión no se propaga** (para borrar de verdad, hazlo a mano en
  ambos lados).
- **Gana el más nuevo**, pero **antes de sobrescribir** guarda la versión
  anterior en `.sgdp-papelera/<fecha>/` del lado sobrescrito (recuperable).
- Si dos versiones **difieren** y sus fechas están tan cerca que no se sabe
  cuál es más nueva, **conserva AMBAS** (una queda como
  `nombre (conflicto LAPTOP …).pdf` / `nombre (conflicto USB …).pdf`) y **te
  avisa**. Nunca pisa el original.
- Lo ya copiado (mismo tamaño y contenido) se **omite** (no re-descarga).

## Requisitos

- **Python 3** instalado (viene en Linux; en Windows, instálalo desde
  python.org marcando «Add Python to PATH»).

## Cómo usarla

**Autorización:** pedirá la clave del USB (**`2026AM`**).

### Linux / Mac
```bash
./sincronizar_usb.sh            # autodetecta el USB y la carpeta SGDP local
./sincronizar_usb.sh --dry-run  # SIMULA: muestra qué haría, sin escribir nada
```

### Windows
Doble clic en **`sincronizar_usb.bat`** (o desde la consola:
`python main.py`).

### Opciones útiles
```
--dry-run                 Simula; no escribe nada (pruébalo la primera vez).
--local  RUTA             Carpeta SGDP en la laptop (si no, se autodetecta
                          ~/Documentos/SGDP).
--usb    RUTA             Carpeta/unidad del USB (si no, se autodetecta).
--si                      No pedir confirmación antes de aplicar.
--clave  CLAVE            Clave de autorización (si no, se pregunta).
```

Ejemplo indicando todo a mano:
```bash
./sincronizar_usb.sh --local ~/Documentos/SGDP --usb /media/usuario/KINGSTON
```

## Recomendación

1. La **primera vez**, corre con `--dry-run` para ver qué hará.
2. Conéctalo, corre la herramienta, espera el resumen, y recién retira el USB
   («expulsar» de forma segura).
3. Si aparece un **conflicto**, abre esa carpeta, compara las dos versiones y
   borra a mano la que no quieras.

> La clave de autorización y otros ajustes (nombre de carpeta, tolerancia de fechas)
> están al inicio de `main.py`, en la sección CONFIGURACIÓN.

## Límite honesto

- **Nunca borra**: una supresión no se propaga; lo sobrescrito va a la papelera `.sgdp-papelera/<fecha>/` del lado que pierde.
- **Gana el más nuevo; en empate conserva ambos** como «(conflicto …)» y avisa: resolver es manual.
- **La clave de autorización vive en el código** (`main.py`, sección CONFIGURACIÓN; `SGDP_USB_CLAVE` la evita en modo no interactivo): no hay `.env` ni perfil.
- **No sigue el patrón `main` + `config` + `lib`** (un solo archivo con lanzadores `.sh` y `.bat`): vino de otro repo el 2026-09-15 y se aceptó así.
- **No simula por defecto**: `--dry-run` la primera vez.