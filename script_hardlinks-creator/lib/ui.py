"""
lib/ui.py — Terminal UI helpers for hardlinks-creator.

All formatted output (headers, separators, status messages) lives here
so the business logic modules stay free of print() calls.
"""

import lib.logger as C  # Color constants resolved at call time → respects disable_colors()


def print_header(text: str) -> None:
    """Renders a full-width double-line box header."""
    width = 80
    bar = "═" * (width - 2)
    padding = (width - len(text) - 2) // 2
    right_pad = width - len(text) - padding - 2
    print(f"\n{C.BOLD}{C.BLUE}╔{bar}╗{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}║{' ' * padding}{text}{' ' * right_pad}║{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}╚{bar}╝{C.RESET}\n")


def print_separator(char: str = "━") -> None:
    """Renders a single-line separator."""
    print(f"\n{C.GRAY}{char * 80}{C.RESET}\n")


def print_field(label: str, value: str, icon: str = "📋") -> None:
    """Renders a labeled key-value line."""
    print(f"{C.CYAN}{icon} {label}:{C.RESET} {C.BOLD}{value}{C.RESET}")


def print_success(text: str) -> None:
    print(f"{C.GREEN}✅ {text}{C.RESET}")


def print_warning(text: str) -> None:
    print(f"{C.YELLOW}⚠️  {text}{C.RESET}")


def print_error(text: str) -> None:
    print(f"{C.RED}❌ {text}{C.RESET}")


def print_info(text: str) -> None:
    print(f"{C.CYAN}ℹ️  {text}{C.RESET}")


def print_skip(text: str) -> None:
    print(f"{C.GRAY}⏭️  {text}{C.RESET}")


def print_group_header(group_number: int, file_hash: str) -> None:
    """Renders the section header for a single hash group."""
    print(
        f"{C.BOLD}{C.BLUE}🔍 GRUPO #{group_number}{C.RESET}"
        f"  {C.GRAY}Hash: {file_hash[:16]}...{C.RESET}\n"
    )


def print_summary(stats: dict) -> None:
    """Renders the final operations summary box."""
    print_separator()
    print_header("RESUMEN DE OPERACIONES")

    rows = [
        (C.GREEN,  "✅ Grupos creados",      stats["groups_created"]),
        (C.CYAN,   "📝 Hard links creados",  stats["links_created"]),
        (C.GRAY,   "⏭️  Ya enlazados (omit)", stats["files_skipped"]),
        (C.YELLOW, "⚠️  Grupos omitidos",     stats["groups_skipped"]),
    ]
    if stats["errors"] > 0:
        rows.append((C.RED, "❌ Errores", stats["errors"]))

    inner_width = 76
    border = f"{C.BOLD}{C.BLUE}"
    print(f"{border}╠{'═' * inner_width}╣{C.RESET}")
    for color, label, value in rows:
        content = f"  {color}{label}:{C.RESET} {C.BOLD}{value}{C.RESET}"
        # Strip ANSI for length calculation
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        visible_len = len(ansi_escape.sub("", content))
        pad = inner_width - visible_len
        print(f"{border}║{C.RESET}{content}{' ' * max(pad, 0)}{border}║{C.RESET}")
    print(f"{border}╚{'═' * inner_width}╝{C.RESET}")

    if stats["groups_created"] > 0:
        print(f"\n{C.GREEN}{C.BOLD}✨ ¡Proceso completado exitosamente!{C.RESET}")
        print(f"{C.GRAY}   Usa hardlinks-detector para verificar los enlaces creados.{C.RESET}\n")
    elif stats["groups_skipped"] > 0:
        print(f"\n{C.YELLOW}ℹ️  Completado sin cambios (grupos omitidos por el usuario).{C.RESET}\n")
    else:
        print(f"\n{C.CYAN}ℹ️  No se requirieron cambios.{C.RESET}\n")


def format_size(size_bytes: int) -> str:
    """Returns a human-readable file size string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def confirm_group(group_number: int) -> bool:
    """
    Prompts the user interactively to confirm or skip a group.

    Returns True if the user confirmed (default), False to skip.
    """
    try:
        response = input(
            f"{C.BOLD}¿Crear hard links para este grupo? [S/n]: {C.RESET}"
        ).strip().lower()
        return response not in ("n", "no")
    except EOFError:
        # Non-interactive environment (pipe, CI) — default to confirm
        return True
