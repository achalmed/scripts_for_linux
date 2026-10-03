---
tipo: readme
estado: activo
---
# docs/ — documentación transversal de `scripts_for_linux`: las decisiones del repo y el historial

Cada herramienta se documenta en su carpeta (su `README.md` es su manual); aquí vive solo lo que
no pertenece a una herramienta sola: por qué el repo es como es y lo cumplido.

## Por dónde empezar

| si eres… | empieza por |
|---|---|
| **quien usa** una herramienta | `../README.md` (§Uso) → el `README.md` de la herramienta |
| **quien amplía** una suite o una GUI | `../CLAUDE.md` → `../scripts_filesystem_studio/README.md` o `../scripts_git_studio/README.md` → [decisiones.md](decisiones.md) §2 |
| **quien mantiene** el repo | [decisiones.md](decisiones.md) (con §Pendientes) → `core/README.md` y `core/suite.schema.yml` |
| quien quiere saber **de dónde** salieron las GUI | [historial/README.md](historial/README.md) |

## Cómo se mantiene

- Lo de una herramienta va a su README; lo transversal, aquí, en el documento de su concepto.
  Nunca un `.md` por sesión, fase o fecha.
- La decisión y su porqué van a [decisiones.md](decisiones.md); lo pendiente, a su §Pendientes.
- Las cantidades que cambian no se escriben: las suites las cuenta `python3 core/suites.py listar`.
- La tabla de abajo la genera `python3 core/docs.py indice scripts_for_linux --aplicar` desde
  `~/Documents`.

## Índice

<!-- docs:inicio -->
| documento | tipo | estado | qué es |
|---|---|---|---|
| [decisiones.md](decisiones.md) | `decision` | `activo` | Decisiones de scripts_for_linux |
| [historial/README.md](historial/README.md) | `readme` | `activo` | docs/historial/ — lo cumplido: las visiones de producto de las que nacieron las GUI |
| [historial/vision-backup-suite.md](historial/vision-backup-suite.md) | `plan` | `hecho` | Visión de producto — Backup Studio (script_backup_suite) (2026-07-13) |
| [historial/vision-filesystem-studio.md](historial/vision-filesystem-studio.md) | `plan` | `hecho` | Visión de producto — Filesystem Studio (2026-07-13) |
| [historial/vision-git-studio.md](historial/vision-git-studio.md) | `plan` | `hecho` | Visión de producto — Git Studio (2026-07-20) |

<sub>Bloque generado por `core/docs.py indice` desde el frontmatter de docs/ (2026-10-03); no se edita a mano.</sub>
<!-- docs:fin -->
