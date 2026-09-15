#!/usr/bin/env python3
"""script_sync_usb/main.py — sincroniza en ambas direcciones una carpeta local con su copia en un USB compartido (papelera y conflictos)."""
# =====================================================================
#  sincronizar_usb.py  --  Sincronización BIDIRECCIONAL laptop <-> USB
#  del SGDP (Despacho del Diputado Alejandro José Manay Pillaca).
# ---------------------------------------------------------------------
#  ¿Para qué?  El navegador (botón «Sincronizar» de la plataforma) solo
#  puede COPIAR del servidor a una carpeta de la laptop, en UNA dirección,
#  y no puede detectar el USB al conectarse. Para compartir documentos
#  entre las laptops de las secretarias con un USB que va y viene, hace
#  falta una herramienta NATIVA. Esta lo es (pedido de Edison 2026-09-01).
#
#  Cada secretaria corre este script en su laptop con el USB conectado; el
#  script sincroniza en AMBAS direcciones la carpeta local del SGDP y la
#  carpeta del USB:
#
#      Laptop Secretaria 1  <->  USB compartido  <->  Laptop Secretaria 2
#
#  SEGURIDAD DE LOS DATOS (nunca se pierde nada):
#    - NO se borra nada: una supresión no se propaga (un archivo que falta
#      en un lado se vuelve a copiar del otro, no se elimina).
#    - Gana el MÁS NUEVO, pero antes de sobrescribir se guarda el anterior
#      en «.sgdp-papelera/<fecha>/» del lado sobrescrito (recuperable).
#    - Si dos versiones DIFIEREN y sus fechas están dentro de la resolución
#      del USB (~2 s), no se asume cuál es más nueva: se CONSERVAN AMBAS
#      como copias «(conflicto …)» y se AVISA.
#    - La identidad es por tamaño + SHA-256: lo ya sincronizado se OMITE.
#
#  AUTORIZACIÓN: pide la clave 2026AM para activar la sincronización
#  (o variable de entorno SGDP_USB_CLAVE para uso no interactivo).
#
#  Uso típico:
#      python3 sincronizar_usb.py                 # autodetecta USB y local
#      python3 sincronizar_usb.py --dry-run       # simula, no escribe nada
#      python3 sincronizar_usb.py --local ~/Documentos/SGDP --usb /media/user/KINGSTON
#
#  Solo usa la biblioteca estándar de Python 3 (no instala nada).
# =====================================================================
from __future__ import annotations

import argparse
import getpass
import hashlib
import re
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ------------------------------ CONFIGURACIÓN (editable) -------------
CLAVE_AUTORIZACION = "2026AM"          # clave para activar la sincronización
NOMBRE_CARPETA = "SGDP"                # nombre por convención de la carpeta
PAPELERA = ".sgdp-papelera"            # respaldos de lo sobrescrito
TOLERANCIA_MTIME = 3.0                 # segundos: FAT redondea a 2 s
# Nombres/carpetas que NUNCA se sincronizan (internos del propio sync y de
# la sincronización web, y cualquier oculto que empiece por «.»).
IGNORAR_EXACTOS = {PAPELERA, ".sgdp-sync.json", ".sgdp-usb-sync.json"}

# ------------------------------ utilidades ---------------------------

def _color(txt: str, code: str) -> str:
    return f"\033[{code}m{txt}\033[0m" if sys.stdout.isatty() else txt


def ok(txt: str) -> str:   return _color(txt, "32")
def aviso(txt: str) -> str: return _color(txt, "33")
def malo(txt: str) -> str:  return _color(txt, "31")
def fuerte(txt: str) -> str: return _color(txt, "1")


def sha256(ruta: Path, _buf: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(_buf), b""):
            h.update(bloque)
    return h.hexdigest()


def _ignorar(rel: Path) -> bool:
    """True si la ruta relativa contiene un segmento oculto o interno."""
    return any(p in IGNORAR_EXACTOS or p.startswith(".") for p in rel.parts)


def indexar(raiz: Path) -> dict[str, Path]:
    """{ruta_relativa_posix -> Path absoluto} de los ARCHIVOS bajo `raiz`,
    saltando ocultos y carpetas internas."""
    salida: dict[str, Path] = {}
    for base, dirs, files in os.walk(raiz):
        # Podar carpetas ocultas/internas para no descender en ellas.
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORAR_EXACTOS]
        for nombre in files:
            p = Path(base) / nombre
            rel = p.relative_to(raiz)
            if _ignorar(rel):
                continue
            salida[rel.as_posix()] = p
    return salida


def identicos(a: Path, b: Path) -> bool:
    """Mismo contenido: primero por tamaño (barato), luego por SHA-256."""
    sa, sb = a.stat(), b.stat()
    if sa.st_size != sb.st_size:
        return False
    return sha256(a) == sha256(b)


# ------------------------------ detección ----------------------------

def detectar_usb() -> list[Path]:
    """Puntos de montaje candidatos de unidades extraíbles, por sistema."""
    cands: list[Path] = []
    so = sys.platform
    if so.startswith("linux"):
        usuario = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
        for base in (f"/media/{usuario}", f"/run/media/{usuario}", "/media", "/mnt"):
            d = Path(base)
            if d.is_dir():
                cands += [x for x in d.iterdir() if x.is_dir()]
    elif so == "darwin":
        vol = Path("/Volumes")
        if vol.is_dir():
            # Excluir el disco del sistema (suele ser «Macintosh HD»).
            cands += [x for x in vol.iterdir() if x.is_dir() and x.name != "Macintosh HD"]
    elif so.startswith("win"):
        try:
            import ctypes

            DRIVE_REMOVABLE = 2
            k32 = ctypes.windll.kernel32
            for letra in "DEFGHIJKLMNOPQRSTUVWXYZ":
                raiz = f"{letra}:\\"
                if os.path.exists(raiz) and k32.GetDriveTypeW(raiz) == DRIVE_REMOVABLE:
                    cands.append(Path(raiz))
        except Exception:
            pass
    # Solo los escribibles.
    return [c for c in cands if os.access(c, os.W_OK)]


def detectar_local() -> Path | None:
    """Carpeta SGDP local por convención (donde la web deja la copia)."""
    hogar = Path.home()
    for base in ("Documentos", "Documents", ""):
        cand = (hogar / base / NOMBRE_CARPETA) if base else (hogar / NOMBRE_CARPETA)
        if cand.is_dir():
            return cand
    return None


def elegir(cands: list[Path], que: str) -> Path | None:
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    print(f"\nSe encontraron varias opciones de {que}:")
    for i, c in enumerate(cands, 1):
        print(f"  {i}) {c}")
    try:
        n = int(input(f"Elige el número de {que} [1-{len(cands)}]: ").strip())
        return cands[n - 1] if 1 <= n <= len(cands) else None
    except (ValueError, IndexError, EOFError):
        return None


# ------------------------------ sincronización -----------------------

class Plan:
    def __init__(self) -> None:
        self.a_usb: list[str] = []       # copiar laptop -> USB
        self.a_local: list[str] = []     # copiar USB -> laptop
        self.conflictos: list[str] = []  # ambos cambiaron, fechas ambiguas
        self.iguales = 0                 # ya al día


def _copiar(origen: Path, destino: Path, dry: bool) -> None:
    if dry:
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        _a_papelera(destino, dry)
    shutil.copy2(origen, destino)  # copy2 preserva la fecha de modificación


def _a_papelera(archivo: Path, dry: bool, raiz: Path | None = None) -> None:
    """Mueve `archivo` a la papelera del SGDP de su lado (recuperable)."""
    if dry or not archivo.exists():
        return
    # Ubicar la papelera en la raíz del árbol al que pertenece el archivo.
    base = raiz or _raiz_de(archivo)
    sello = datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = base / PAPELERA / sello / archivo.name
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(archivo), str(destino))


_RAICES: list[Path] = []  # se rellena en sincronizar() para _raiz_de()


def _raiz_de(archivo: Path) -> Path:
    for r in _RAICES:
        try:
            archivo.relative_to(r)
            return r
        except ValueError:
            continue
    return archivo.parent


def _copia_conflicto(origen: Path, carpeta_destino_raiz: Path, rel: str, etiqueta: str, dry: bool) -> str | None:
    """Copia `origen` al otro lado como «… (conflicto ETIQUETA <hash>).ext», SIN
    tocar el original de ese lado. El sufijo es un hash del CONTENIDO
    (determinista): si esa copia ya existe idéntica, no se duplica —así una
    corrida repetida sobre un conflicto sin resolver no genera copias nuevas—.
    Devuelve el nombre creado, o None si ya estaba preservada."""
    rel_p = Path(rel)
    h8 = sha256(origen)[:8]
    nuevo = rel_p.with_name(f"{rel_p.stem} (conflicto {etiqueta} {h8}){rel_p.suffix}")
    destino = carpeta_destino_raiz / nuevo
    if destino.exists() and identicos(origen, destino):
        return None
    if not dry:
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, destino)
    return nuevo.as_posix()


# Nombres de la convención vigente del sistema (SERIE-NUMERO-PERIODO_Asunto y
# derivados ADJ/CR/FIRM/RESP/EXP). Ver backend/app/servicios/nombres.py.
CONVENCION = re.compile(
    r"^(OF|OM|OMB|OB|CARTA|MEM|INF|SOL|ACT|ADJ|CR|FIRM|RESP|EXP)-", re.IGNORECASE
)


def retirar_versiones_anteriores(raiz: Path, dry: bool) -> list[str]:
    """Aparta las copias con el nombre ANTIGUO cuando el MISMO archivo ya está
    con el nombre nuevo (Edison 2026-09-08: «no queremos copias sueltas en
    ningún lado»).

    El renombrado masivo del 2026-09-08 dejó, en las carpetas ya copiadas a un
    USB o a una laptop, el archivo con su nombre viejo. Sin esto la
    sincronización los daría por archivos que faltan en el otro lado y los
    volvería a copiar —incluso de vuelta al servidor—, multiplicando las
    copias en lugar de limpiarlas.

    Criterio DELIBERADAMENTE estrecho, porque esto mueve archivos del usuario:
      · solo PDF;
      · solo si en la MISMA carpeta hay otro archivo con el MISMO contenido
        (sha256 idéntico) cuyo nombre sí sigue la convención vigente;
      · el sobrante se MUEVE a la papelera del SGDP (recuperable), nunca se
        borra.
    Un archivo sin gemelo exacto no se toca jamás, aunque su nombre sea viejo:
    podría ser el único ejemplar de algo.
    """
    if not raiz.is_dir():
        return []
    retirados: list[str] = []
    for carpeta_actual, _dirs, archivos in os.walk(raiz):
        base = Path(carpeta_actual)
        if PAPELERA in base.parts:
            continue
        pdfs = [base / n for n in archivos if n.lower().endswith(".pdf")]
        if len(pdfs) < 2:
            continue
        por_hash: dict[str, list[Path]] = {}
        for ruta in pdfs:
            por_hash.setdefault(sha256(ruta), []).append(ruta)
        for gemelos in por_hash.values():
            if len(gemelos) < 2:
                continue
            vigentes = [g for g in gemelos if CONVENCION.match(g.name)]
            sobrantes = [g for g in gemelos if not CONVENCION.match(g.name)]
            # Sin un ejemplar con el nombre nuevo no hay nada que retirar.
            if not vigentes or not sobrantes:
                continue
            for viejo in sobrantes:
                retirados.append(str(viejo.relative_to(raiz)))
                _a_papelera(viejo, dry, raiz)
    return retirados


def sincronizar(local: Path, usb: Path, dry: bool) -> Plan:
    global _RAICES
    _RAICES = [local, usb]
    # Antes de comparar: apartar las copias con el nombre anterior que ya
    # existen con el nombre nuevo. Si no, el lado que aún tiene la vieja se la
    # «regalaría» al otro y las copias se multiplicarían.
    for lado, raiz in (("laptop", local), ("USB", usb)):
        sobrantes = retirar_versiones_anteriores(raiz, dry)
        if sobrantes:
            print(
                aviso(
                    f"  {len(sobrantes)} copia(s) con el nombre anterior apartada(s) "
                    f"en {lado} (a {PAPELERA}/)."
                )
            )
    idx_local = indexar(local)
    idx_usb = indexar(usb)
    plan = Plan()

    for rel in sorted(set(idx_local) | set(idx_usb)):
        pl = idx_local.get(rel)
        pu = idx_usb.get(rel)

        if pl and not pu:                       # solo en la laptop -> al USB
            plan.a_usb.append(rel)
            _copiar(pl, usb / rel, dry)
            continue
        if pu and not pl:                       # solo en el USB -> a la laptop
            plan.a_local.append(rel)
            _copiar(pu, local / rel, dry)
            continue

        # En ambos lados: ¿idénticos?
        assert pl and pu
        if identicos(pl, pu):
            plan.iguales += 1
            continue

        # Difieren: decidir por fecha de modificación.
        ml, mu = pl.stat().st_mtime, pu.stat().st_mtime
        if abs(ml - mu) <= TOLERANCIA_MTIME:
            # Ambiguo (no se sabe cuál es más nuevo): conservar AMBAS versiones
            # y avisar. Nunca se pisa el original de ningún lado.
            n1 = _copia_conflicto(pl, usb, rel, "LAPTOP", dry)
            n2 = _copia_conflicto(pu, local, rel, "USB", dry)
            detalle = " / ".join(x for x in (n1, n2) if x) or "(ya preservado)"
            plan.conflictos.append(f"{rel}  ->  {detalle}")
        elif ml > mu:                           # la laptop es más nueva
            plan.a_usb.append(rel)
            _copiar(pl, usb / rel, dry)         # respalda el del USB en su papelera
        else:                                    # el USB es más nuevo
            plan.a_local.append(rel)
            _copiar(pu, local / rel, dry)        # respalda el de la laptop
    return plan


# ------------------------------ interfaz -----------------------------

def autorizar(clave_cli: str | None) -> bool:
    esperada = CLAVE_AUTORIZACION
    dada = clave_cli or os.environ.get("SGDP_USB_CLAVE")
    if dada is None:
        try:
            dada = getpass.getpass("Clave de autorización del USB: ")
        except (EOFError, KeyboardInterrupt):
            return False
    if dada != esperada:
        print(malo("Clave incorrecta. No se autorizó la sincronización."))
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Sincronización bidireccional laptop <-> USB del SGDP.",
    )
    ap.add_argument("--local", type=Path, help="Carpeta SGDP en la laptop.")
    ap.add_argument("--usb", type=Path, help="Carpeta/unidad del USB compartido.")
    ap.add_argument("--dry-run", action="store_true", help="Simula; no escribe nada.")
    ap.add_argument("--si", action="store_true", help="No pedir confirmación al aplicar.")
    ap.add_argument("--clave", help="Clave de autorización (si no, se pregunta).")
    args = ap.parse_args()

    print(fuerte("== Sincronización USB del SGDP =="))

    # 1) Autorización.
    if not autorizar(args.clave):
        return 1

    # 2) Resolver carpeta local.
    local = args.local or detectar_local()
    if local is None:
        print(malo("No encontré la carpeta SGDP local. Indícala con --local RUTA."))
        print("   (por convención: ~/Documentos/SGDP)")
        return 1
    local = local.expanduser().resolve()
    if not local.is_dir():
        print(malo(f"La carpeta local no existe: {local}"))
        return 1

    # 3) Resolver carpeta del USB (si es la raíz de la unidad, usar <USB>/SGDP).
    if args.usb:
        usb = args.usb.expanduser().resolve()
    else:
        montado = elegir(detectar_usb(), "USB")
        if montado is None:
            print(malo("No detecté un USB. Conéctalo o indícalo con --usb RUTA."))
            return 1
        usb = montado
    if usb.is_dir() and usb.name != NOMBRE_CARPETA and not (usb / "Oficios").is_dir():
        usb = usb / NOMBRE_CARPETA
    if not args.dry_run:
        usb.mkdir(parents=True, exist_ok=True)
    elif not usb.exists():
        print(aviso(f"(dry-run) Se crearía la carpeta del USB: {usb}"))

    if local == usb:
        print(malo("La carpeta local y la del USB son la misma. Aborto."))
        return 1

    print(f"  Laptop: {fuerte(str(local))}")
    print(f"  USB:    {fuerte(str(usb))}")
    if args.dry_run:
        print(aviso("  Modo simulación (--dry-run): no se escribirá nada."))

    # 4) Confirmación (salvo --si o --dry-run): primero un plan «en seco».
    if not args.dry_run and not args.si:
        previo = sincronizar(local, usb, dry=True)
        print(
            f"\n  Se copiarán {fuerte(str(len(previo.a_usb)))} a USB, "
            f"{fuerte(str(len(previo.a_local)))} a la laptop, "
            f"{fuerte(str(len(previo.conflictos)))} conflicto(s); "
            f"{previo.iguales} ya al día."
        )
        try:
            if input("¿Aplicar la sincronización? [s/N]: ").strip().lower() not in ("s", "si", "sí"):
                print("Cancelado.")
                return 0
        except (EOFError, KeyboardInterrupt):
            print("\nCancelado.")
            return 0

    # 5) Sincronizar.
    plan = sincronizar(local, usb, dry=args.dry_run)

    # 6) Reporte.
    print("\n" + fuerte("Resumen:"))
    print(ok(f"  → al USB:    {len(plan.a_usb)}"))
    print(ok(f"  ← a laptop:  {len(plan.a_local)}"))
    print(f"  = ya al día: {plan.iguales}")
    if plan.conflictos:
        print(aviso(f"  ⚠ conflictos (se conservaron AMBAS versiones): {len(plan.conflictos)}"))
        for c in plan.conflictos:
            print(aviso(f"      {c}"))
        print(aviso("    Revisa esas parejas y borra la que no quieras (a mano)."))
    if args.dry_run:
        print(aviso("\n(dry-run) No se escribió nada. Quita --dry-run para aplicar."))
    else:
        print(ok("\nListo. Lo sobrescrito quedó respaldado en «.sgdp-papelera/»."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
