# Reporte de Auditoría — Hard Links

- **Fecha:** 2026-07-02
- **Hora:** 22:49:21
- **Directorio analizado:** `/tmp/claude-1000/-home-achalmaedison-Documents-scripts-for-linux/33bc565f-59db-428c-bf10-cf6e3b5f4515/scratchpad/hltest`
- **Tiempo de ejecución:** 0 s
- **Versión:** hardlinks-detector 3.1.0
- **Sistema operativo:** Ubuntu 26.04 LTS

> Línea base del sistema de hard links. Este archivo se sobrescribe en cada
> ejecución; usa `git diff` para comparar con ejecuciones anteriores.

## Resumen Ejecutivo

| Indicador                        | Valor |
| -------------------------------- | ----: |
| Conjuntos de hard links          |     6 |
| Hard links (suma de enlaces)     |    15 |
| Archivos encontrados en el árbol |    14 |
| Espacio usado                    | 116 B |
| Espacio ahorrado                 | 197 B |

## Estado General

- ⚠️ 1 conjunto(s) tienen enlaces fuera del directorio analizado.
- ✅ No se detectaron conjuntos con tamaño 0 bytes.
- ℹ️ 1 archivo(s) crítico(s) con 5 o más enlaces.

## Inventario Completo

|   # | Archivo              | Tipo       | Inodo | Links | Tamaño | Ahorro | Estado     | Observaciones                              |
| --: | -------------------- | ---------- | ----- | ----: | -----: | -----: | ---------- | ------------------------------------------ |
|   1 | `blog/app.js`        | JavaScript | 3493  |     2 |   16 B |   16 B | ✅ OK      | —                                          |
|   2 | `blog/_metadata.yml` | YAML       | 3490  |     5 |   27 B |  108 B | ✅ OK      | —                                          |
|   3 | `blog/README.md`     | Markdown   | 3491  |     2 |   17 B |   17 B | ✅ OK      | —                                          |
|   4 | `blog/shared.qmd`    | QMD        | 3496  |     2 |   15 B |   15 B | ⚠️ Parcial | 1 enlace(s) fuera del directorio analizado |
|   5 | `deploy.sh`          | Scripts    | 3494  |     2 |   20 B |   20 B | ✅ OK      | —                                          |
|   6 | `docs/styles.scss`   | SCSS       | 3492  |     2 |   21 B |   21 B | ✅ OK      | —                                          |

## Agrupación por categorías

### SCSS

| Archivo            | Inodo | Links | Tamaño | Ahorro |
| ------------------ | ----- | ----: | -----: | -----: |
| `docs/styles.scss` | 3492  |     2 |   21 B |   21 B |

### JavaScript

| Archivo       | Inodo | Links | Tamaño | Ahorro |
| ------------- | ----- | ----: | -----: | -----: |
| `blog/app.js` | 3493  |     2 |   16 B |   16 B |

### YAML

| Archivo              | Inodo | Links | Tamaño | Ahorro |
| -------------------- | ----- | ----: | -----: | -----: |
| `blog/_metadata.yml` | 3490  |     5 |   27 B |  108 B |

### Markdown

| Archivo          | Inodo | Links | Tamaño | Ahorro |
| ---------------- | ----- | ----: | -----: | -----: |
| `blog/README.md` | 3491  |     2 |   17 B |   17 B |

### QMD

| Archivo           | Inodo | Links | Tamaño | Ahorro |
| ----------------- | ----- | ----: | -----: | -----: |
| `blog/shared.qmd` | 3496  |     2 |   15 B |   15 B |

### Scripts

| Archivo     | Inodo | Links | Tamaño | Ahorro |
| ----------- | ----- | ----: | -----: | -----: |
| `deploy.sh` | 3494  |     2 |   20 B |   20 B |

## Top archivos más compartidos

| Posición | Archivo              | Links | Tamaño | Ahorro |
| -------: | -------------------- | ----: | -----: | -----: |
|        1 | `blog/_metadata.yml` |     5 |   27 B |  108 B |
|        2 | `blog/app.js`        |     2 |   16 B |   16 B |
|        3 | `blog/README.md`     |     2 |   17 B |   17 B |
|        4 | `blog/shared.qmd`    |     2 |   15 B |   15 B |
|        5 | `deploy.sh`          |     2 |   20 B |   20 B |
|        6 | `docs/styles.scss`   |     2 |   21 B |   21 B |

## Archivos críticos

Archivos con **5 o más enlaces**: modificar su contenido afecta a todas sus copias.

| Archivo              | Inodo | Links | Impacto de una modificación |
| -------------------- | ----- | ----: | --------------------------- |
| `blog/_metadata.yml` | 3490  |     5 | Afecta a 5 ubicaciones      |

## Resumen por directorios

| Proyecto | Archivos compartidos | Espacio ahorrado |
| -------- | -------------------: | ---------------: |
| `blog`   |                    5 |             27 B |
| `docs`   |                    5 |             27 B |
| `(raíz)` |                    1 |              0 B |
| `theme`  |                    3 |              0 B |

> El ahorro se atribuye al directorio donde existen copias duplicadas
> del mismo inodo (tamaño × copias adicionales dentro del directorio).

## Checklist de auditoría

- [x] Escaneo completado (6 conjunto(s) inventariado(s))
- [ ] Todos los conjuntos están completos dentro del directorio analizado
- [x] Ningún conjunto con tamaño 0 bytes
- [ ] Comparado con la ejecución anterior: `git diff -- reports/hardlinks-report.md`
- [ ] Revisados los conjuntos marcados como «Parcial» (si existen)
- [ ] Verificado que los archivos críticos siguen sincronizados

## Comandos útiles

```bash
# Ver inodo, tamaño y número de enlaces de un archivo
stat -c '%i %s %h %n' archivo

# Localizar todos los enlaces de un inodo específico
find '/tmp/claude-1000/-home-achalmaedison-Documents-scripts-for-linux/33bc565f-59db-428c-bf10-cf6e3b5f4515/scratchpad/hltest' -inum INODO

# Localizar todos los enlaces del mismo archivo físico
find '/tmp/claude-1000/-home-achalmaedison-Documents-scripts-for-linux/33bc565f-59db-428c-bf10-cf6e3b5f4515/scratchpad/hltest' -samefile archivo

# Listar todos los archivos con más de un hard link
find '/tmp/claude-1000/-home-achalmaedison-Documents-scripts-for-linux/33bc565f-59db-428c-bf10-cf6e3b5f4515/scratchpad/hltest' -type f -links +1
```

## Conclusión

El análisis identificó **6 conjunto(s)** de hard links que agrupan **14 archivo(s)**, con un ahorro total de **197 B** en disco.

Se detectaron puntos de atención: 1 conjunto(s) con enlaces externos y 0 con tamaño 0.
Revisa la columna «Observaciones» del inventario antes de la próxima ejecución.
