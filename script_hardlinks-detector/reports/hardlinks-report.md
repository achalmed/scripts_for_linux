# Reporte de Auditoría — Hard Links

- **Fecha:** 2026-07-02
- **Hora:** 23:07:38
- **Directorio analizado:** `/home/achalmaedison/Documents`
- **Tiempo de ejecución:** 1 s
- **Versión:** hardlinks-detector 3.1.0
- **Sistema operativo:** Ubuntu 26.04 LTS

> Línea base del sistema de hard links. Este archivo se sobrescribe en cada
> ejecución; usa `git diff` para comparar con ejecuciones anteriores.

## Resumen Ejecutivo

| Indicador                        |  Valor |
| -------------------------------- | -----: |
| Conjuntos de hard links          |     68 |
| Hard links (suma de enlaces)     |    824 |
| Archivos encontrados en el árbol |    824 |
| Espacio usado                    | 207 KB |
| Espacio ahorrado                 |   2 MB |

## Estado General

- ✅ Todos los conjuntos están completos dentro del directorio analizado.
- ✅ No se detectaron conjuntos con tamaño 0 bytes.
- ℹ️ 66 archivo(s) crítico(s) con 5 o más enlaces.

## Inventario Completo

|   # | Archivo                                                                  | Tipo       | Inodo   | Links | Tamaño | Ahorro | Estado | Observaciones |
| --: | ------------------------------------------------------------------------ | ---------- | ------- | ----: | -----: | -----: | ------ | ------------- |
|   1 | `pub_actus-mercator/404.qmd`                                             | QMD        | 5640352 |    12 |  259 B |   2 KB | ✅ OK  | —             |
|   2 | `pub_actus-mercator/assets/css/components/bibbase.css`                   | Otros      | 6162818 |    12 |   2 KB |  26 KB | ✅ OK  | —             |
|   3 | `pub_actus-mercator/assets/css/pages/about.css`                          | Otros      | 6162817 |    12 |   2 KB |  30 KB | ✅ OK  | —             |
|   4 | `pub_actus-mercator/assets/css/pages/contact.css`                        | Otros      | 6162816 |    12 |   2 KB |  29 KB | ✅ OK  | —             |
|   5 | `pub_actus-mercator/assets/css/pages/home.css`                           | Otros      | 6162814 |    12 |   7 KB |  83 KB | ✅ OK  | —             |
|   6 | `pub_actus-mercator/assets/css/pages/listing.css`                        | Otros      | 6162815 |    12 |   2 KB |  23 KB | ✅ OK  | —             |
|   7 | `pub_actus-mercator/assets/interactions.html`                            | HTML       | 5639034 |    12 |   1 KB |  11 KB | ✅ OK  | —             |
|   8 | `pub_actus-mercator/assets/js/cursor.js`                                 | JavaScript | 6162819 |    12 |   1 KB |  17 KB | ✅ OK  | —             |
|   9 | `pub_actus-mercator/assets/js/hero.js`                                   | JavaScript | 6162821 |    12 |   1 KB |  19 KB | ✅ OK  | —             |
|  10 | `pub_actus-mercator/assets/js/navbar.js`                                 | JavaScript | 6162823 |    12 |  974 B |  10 KB | ✅ OK  | —             |
|  11 | `pub_actus-mercator/assets/js/README.md`                                 | Markdown   | 6162822 |    12 |   2 KB |  23 KB | ✅ OK  | —             |
|  12 | `pub_actus-mercator/assets/js/scroll-effects.js`                         | JavaScript | 6162820 |    12 |   1 KB |  18 KB | ✅ OK  | —             |
|  13 | `pub_actus-mercator/assets/scss/00-settings/_bootstrap.scss`             | SCSS       | 6162846 |    12 |   1 KB |  21 KB | ✅ OK  | —             |
|  14 | `pub_actus-mercator/assets/scss/00-settings/_layout.scss`                | SCSS       | 6162845 |    12 |  882 B |   9 KB | ✅ OK  | —             |
|  15 | `pub_actus-mercator/assets/scss/00-settings/_palette-dark.scss`          | SCSS       | 6162850 |    12 |   1 KB |  17 KB | ✅ OK  | —             |
|  16 | `pub_actus-mercator/assets/scss/00-settings/_palette-light.scss`         | SCSS       | 6162848 |    12 |   1 KB |  20 KB | ✅ OK  | —             |
|  17 | `pub_actus-mercator/assets/scss/00-settings/_tokens-dark.scss`           | SCSS       | 6162847 |    12 |   5 KB |  56 KB | ✅ OK  | —             |
|  18 | `pub_actus-mercator/assets/scss/00-settings/_tokens-light.scss`          | SCSS       | 6162849 |    12 |   5 KB |  60 KB | ✅ OK  | —             |
|  19 | `pub_actus-mercator/assets/scss/00-settings/_typography.scss`            | SCSS       | 6162851 |    12 |   1 KB |  18 KB | ✅ OK  | —             |
|  20 | `pub_actus-mercator/assets/scss/01-tools/_mixins.scss`                   | SCSS       | 6162840 |    12 |   1 KB |  14 KB | ✅ OK  | —             |
|  21 | `pub_actus-mercator/assets/scss/02-base/_fonts.scss`                     | SCSS       | 6162828 |    12 |   3 KB |  42 KB | ✅ OK  | —             |
|  22 | `pub_actus-mercator/assets/scss/02-base/_reset.scss`                     | SCSS       | 6162830 |    12 |   1 KB |  12 KB | ✅ OK  | —             |
|  23 | `pub_actus-mercator/assets/scss/02-base/_root.scss`                      | SCSS       | 6162827 |    12 |   1 KB |  16 KB | ✅ OK  | —             |
|  24 | `pub_actus-mercator/assets/scss/02-base/_typography.scss`                | SCSS       | 6162829 |    12 |   3 KB |  37 KB | ✅ OK  | —             |
|  25 | `pub_actus-mercator/assets/scss/03-layout/_footer.scss`                  | SCSS       | 6162843 |    12 |   1 KB |  14 KB | ✅ OK  | —             |
|  26 | `pub_actus-mercator/assets/scss/03-layout/_navbar.scss`                  | SCSS       | 6162844 |    12 |   2 KB |  32 KB | ✅ OK  | —             |
|  27 | `pub_actus-mercator/assets/scss/03-layout/_responsive.scss`              | SCSS       | 6162841 |    12 |   1 KB |  14 KB | ✅ OK  | —             |
|  28 | `pub_actus-mercator/assets/scss/03-layout/_toc.scss`                     | SCSS       | 6162842 |    12 |   4 KB |  52 KB | ✅ OK  | —             |
|  29 | `pub_actus-mercator/assets/scss/04-components/_buttons.scss`             | SCSS       | 6162860 |    12 |   1 KB |  15 KB | ✅ OK  | —             |
|  30 | `pub_actus-mercator/assets/scss/04-components/_callouts.scss`            | SCSS       | 6162861 |    12 |   1 KB |  11 KB | ✅ OK  | —             |
|  31 | `pub_actus-mercator/assets/scss/04-components/_citations.scss`           | SCSS       | 6162858 |    12 |   1 KB |  13 KB | ✅ OK  | —             |
|  32 | `pub_actus-mercator/assets/scss/04-components/_code.scss`                | SCSS       | 6162862 |    12 |   1 KB |  21 KB | ✅ OK  | —             |
|  33 | `pub_actus-mercator/assets/scss/04-components/_floats.scss`              | SCSS       | 6160717 |    12 |   2 KB |  28 KB | ✅ OK  | —             |
|  34 | `pub_actus-mercator/assets/scss/04-components/_listings.scss`            | SCSS       | 6162854 |    12 |   2 KB |  30 KB | ✅ OK  | —             |
|  35 | `pub_actus-mercator/assets/scss/04-components/_math.scss`                | SCSS       | 6162857 |    12 |  781 B |   8 KB | ✅ OK  | —             |
|  36 | `pub_actus-mercator/assets/scss/04-components/_pagination.scss`          | SCSS       | 6162855 |    12 |   1 KB |  12 KB | ✅ OK  | —             |
|  37 | `pub_actus-mercator/assets/scss/04-components/_search.scss`              | SCSS       | 6162864 |    12 |  848 B |   9 KB | ✅ OK  | —             |
|  38 | `pub_actus-mercator/assets/scss/04-components/_section-numbers.scss`     | SCSS       | 6162856 |    12 |   2 KB |  27 KB | ✅ OK  | —             |
|  39 | `pub_actus-mercator/assets/scss/04-components/_social.scss`              | SCSS       | 6162859 |    12 |  866 B |   9 KB | ✅ OK  | —             |
|  40 | `pub_actus-mercator/assets/scss/04-components/_tables.scss`              | SCSS       | 6162853 |    12 |   1 KB |  16 KB | ✅ OK  | —             |
|  41 | `pub_actus-mercator/assets/scss/04-components/_title-block.scss`         | SCSS       | 6162863 |    12 |   1 KB |  20 KB | ✅ OK  | —             |
|  42 | `pub_actus-mercator/assets/scss/05-interactions/_microinteractions.scss` | SCSS       | 6162852 |    12 |   2 KB |  23 KB | ✅ OK  | —             |
|  43 | `pub_actus-mercator/assets/scss/05-pages/about.scss`                     | SCSS       | 6162839 |    12 |   3 KB |  37 KB | ✅ OK  | —             |
|  44 | `pub_actus-mercator/assets/scss/05-pages/_blog.scss`                     | SCSS       | 6162835 |    12 |  956 B |  10 KB | ✅ OK  | —             |
|  45 | `pub_actus-mercator/assets/scss/05-pages/contact.scss`                   | SCSS       | 6162836 |    12 |   3 KB |  36 KB | ✅ OK  | —             |
|  46 | `pub_actus-mercator/assets/scss/05-pages/_courses.scss`                  | SCSS       | 6162837 |    12 |  946 B |  10 KB | ✅ OK  | —             |
|  47 | `pub_actus-mercator/assets/scss/05-pages/home.scss`                      | SCSS       | 6162833 |    12 |   8 KB |  91 KB | ✅ OK  | —             |
|  48 | `pub_actus-mercator/assets/scss/05-pages/listing.scss`                   | SCSS       | 6162838 |    12 |   2 KB |  31 KB | ✅ OK  | —             |
|  49 | `pub_actus-mercator/assets/scss/05-pages/_post.scss`                     | SCSS       | 6162831 |    12 |  935 B |  10 KB | ✅ OK  | —             |
|  50 | `pub_actus-mercator/assets/scss/05-pages/_projects.scss`                 | SCSS       | 6162834 |    12 |  940 B |  10 KB | ✅ OK  | —             |
|  51 | `pub_actus-mercator/assets/scss/05-pages/_publications.scss`             | SCSS       | 6162832 |    12 | 1022 B |  10 KB | ✅ OK  | —             |
|  52 | `pub_actus-mercator/assets/scss/06-themes/_dark-adjustments.scss`        | SCSS       | 6162865 |    12 |   1 KB |  20 KB | ✅ OK  | —             |
|  53 | `pub_actus-mercator/assets/scss/README.md`                               | Markdown   | 6162826 |    12 |   6 KB |  66 KB | ✅ OK  | —             |
|  54 | `pub_actus-mercator/assets/scss/theme-dark.scss`                         | SCSS       | 6162824 |    12 |   2 KB |  23 KB | ✅ OK  | —             |
|  55 | `pub_actus-mercator/assets/scss/theme-light.scss`                        | SCSS       | 6162825 |    12 |   1 KB |  21 KB | ✅ OK  | —             |
|  56 | `pub_actus-mercator/_contenido-final.qmd`                                | QMD        | 5640357 |    13 |  106 B |   1 KB | ✅ OK  | —             |
|  57 | `pub_actus-mercator/_contenido-inicio.qmd`                               | QMD        | 5640358 |    13 |  197 B |   2 KB | ✅ OK  | —             |
|  58 | `pub_actus-mercator/docs/README.md`                                      | Markdown   | 5653394 |    12 |  14 KB | 164 KB | ✅ OK  | —             |
|  59 | `pub_actus-mercator/_filters/apa-floats-html.lua`                        | Lua        | 5653238 |    12 |   6 KB |  71 KB | ✅ OK  | —             |
|  60 | `pub_actus-mercator/_filters/_metadata-pdf.lua`                          | Lua        | 5653239 |    12 |   1 KB |  13 KB | ✅ OK  | —             |
|  61 | `pub_actus-mercator/.gitignore`                                          | Otros      | 5640285 |    12 |   7 KB |  84 KB | ✅ OK  | —             |
|  62 | `pub_actus-mercator/inteligencia-comercial/_metadata.yml`                | YAML       | 5647618 |    37 |  15 KB | 571 KB | ✅ OK  | —             |
|  63 | `pub_actus-mercator/LICENSE`                                             | Otros      | 5640354 |    12 |  16 KB | 179 KB | ✅ OK  | —             |
|  64 | `pub_actus-mercator/_partials/title-block-link-buttons/title-block.html` | HTML       | 5640442 |    12 |   2 KB |  25 KB | ✅ OK  | —             |
|  65 | `pub_actus-mercator/scripts/build-page-css.sh`                           | Scripts    | 6162951 |    12 |   2 KB |  24 KB | ✅ OK  | —             |
|  66 | `pub_actus-mercator/SECURITY.md`                                         | Markdown   | 5640356 |    12 |  619 B |   6 KB | ✅ OK  | —             |
|  67 | `website-achalma/blog/posts/_metadata.yml`                               | YAML       | 5637346 |     3 |  14 KB |  29 KB | ✅ OK  | —             |
|  68 | `website-achalma/publication/_metadata.yml`                              | YAML       | 5637343 |     2 |  391 B |  391 B | ✅ OK  | —             |

## Agrupación por categorías

### SCSS

| Archivo                                                                  | Inodo   | Links | Tamaño | Ahorro |
| ------------------------------------------------------------------------ | ------- | ----: | -----: | -----: |
| `pub_actus-mercator/assets/scss/00-settings/_bootstrap.scss`             | 6162846 |    12 |   1 KB |  21 KB |
| `pub_actus-mercator/assets/scss/00-settings/_layout.scss`                | 6162845 |    12 |  882 B |   9 KB |
| `pub_actus-mercator/assets/scss/00-settings/_palette-dark.scss`          | 6162850 |    12 |   1 KB |  17 KB |
| `pub_actus-mercator/assets/scss/00-settings/_palette-light.scss`         | 6162848 |    12 |   1 KB |  20 KB |
| `pub_actus-mercator/assets/scss/00-settings/_tokens-dark.scss`           | 6162847 |    12 |   5 KB |  56 KB |
| `pub_actus-mercator/assets/scss/00-settings/_tokens-light.scss`          | 6162849 |    12 |   5 KB |  60 KB |
| `pub_actus-mercator/assets/scss/00-settings/_typography.scss`            | 6162851 |    12 |   1 KB |  18 KB |
| `pub_actus-mercator/assets/scss/01-tools/_mixins.scss`                   | 6162840 |    12 |   1 KB |  14 KB |
| `pub_actus-mercator/assets/scss/02-base/_fonts.scss`                     | 6162828 |    12 |   3 KB |  42 KB |
| `pub_actus-mercator/assets/scss/02-base/_reset.scss`                     | 6162830 |    12 |   1 KB |  12 KB |
| `pub_actus-mercator/assets/scss/02-base/_root.scss`                      | 6162827 |    12 |   1 KB |  16 KB |
| `pub_actus-mercator/assets/scss/02-base/_typography.scss`                | 6162829 |    12 |   3 KB |  37 KB |
| `pub_actus-mercator/assets/scss/03-layout/_footer.scss`                  | 6162843 |    12 |   1 KB |  14 KB |
| `pub_actus-mercator/assets/scss/03-layout/_navbar.scss`                  | 6162844 |    12 |   2 KB |  32 KB |
| `pub_actus-mercator/assets/scss/03-layout/_responsive.scss`              | 6162841 |    12 |   1 KB |  14 KB |
| `pub_actus-mercator/assets/scss/03-layout/_toc.scss`                     | 6162842 |    12 |   4 KB |  52 KB |
| `pub_actus-mercator/assets/scss/04-components/_buttons.scss`             | 6162860 |    12 |   1 KB |  15 KB |
| `pub_actus-mercator/assets/scss/04-components/_callouts.scss`            | 6162861 |    12 |   1 KB |  11 KB |
| `pub_actus-mercator/assets/scss/04-components/_citations.scss`           | 6162858 |    12 |   1 KB |  13 KB |
| `pub_actus-mercator/assets/scss/04-components/_code.scss`                | 6162862 |    12 |   1 KB |  21 KB |
| `pub_actus-mercator/assets/scss/04-components/_floats.scss`              | 6160717 |    12 |   2 KB |  28 KB |
| `pub_actus-mercator/assets/scss/04-components/_listings.scss`            | 6162854 |    12 |   2 KB |  30 KB |
| `pub_actus-mercator/assets/scss/04-components/_math.scss`                | 6162857 |    12 |  781 B |   8 KB |
| `pub_actus-mercator/assets/scss/04-components/_pagination.scss`          | 6162855 |    12 |   1 KB |  12 KB |
| `pub_actus-mercator/assets/scss/04-components/_search.scss`              | 6162864 |    12 |  848 B |   9 KB |
| `pub_actus-mercator/assets/scss/04-components/_section-numbers.scss`     | 6162856 |    12 |   2 KB |  27 KB |
| `pub_actus-mercator/assets/scss/04-components/_social.scss`              | 6162859 |    12 |  866 B |   9 KB |
| `pub_actus-mercator/assets/scss/04-components/_tables.scss`              | 6162853 |    12 |   1 KB |  16 KB |
| `pub_actus-mercator/assets/scss/04-components/_title-block.scss`         | 6162863 |    12 |   1 KB |  20 KB |
| `pub_actus-mercator/assets/scss/05-interactions/_microinteractions.scss` | 6162852 |    12 |   2 KB |  23 KB |
| `pub_actus-mercator/assets/scss/05-pages/about.scss`                     | 6162839 |    12 |   3 KB |  37 KB |
| `pub_actus-mercator/assets/scss/05-pages/_blog.scss`                     | 6162835 |    12 |  956 B |  10 KB |
| `pub_actus-mercator/assets/scss/05-pages/contact.scss`                   | 6162836 |    12 |   3 KB |  36 KB |
| `pub_actus-mercator/assets/scss/05-pages/_courses.scss`                  | 6162837 |    12 |  946 B |  10 KB |
| `pub_actus-mercator/assets/scss/05-pages/home.scss`                      | 6162833 |    12 |   8 KB |  91 KB |
| `pub_actus-mercator/assets/scss/05-pages/listing.scss`                   | 6162838 |    12 |   2 KB |  31 KB |
| `pub_actus-mercator/assets/scss/05-pages/_post.scss`                     | 6162831 |    12 |  935 B |  10 KB |
| `pub_actus-mercator/assets/scss/05-pages/_projects.scss`                 | 6162834 |    12 |  940 B |  10 KB |
| `pub_actus-mercator/assets/scss/05-pages/_publications.scss`             | 6162832 |    12 | 1022 B |  10 KB |
| `pub_actus-mercator/assets/scss/06-themes/_dark-adjustments.scss`        | 6162865 |    12 |   1 KB |  20 KB |
| `pub_actus-mercator/assets/scss/theme-dark.scss`                         | 6162824 |    12 |   2 KB |  23 KB |
| `pub_actus-mercator/assets/scss/theme-light.scss`                        | 6162825 |    12 |   1 KB |  21 KB |

### JavaScript

| Archivo                                          | Inodo   | Links | Tamaño | Ahorro |
| ------------------------------------------------ | ------- | ----: | -----: | -----: |
| `pub_actus-mercator/assets/js/cursor.js`         | 6162819 |    12 |   1 KB |  17 KB |
| `pub_actus-mercator/assets/js/hero.js`           | 6162821 |    12 |   1 KB |  19 KB |
| `pub_actus-mercator/assets/js/navbar.js`         | 6162823 |    12 |  974 B |  10 KB |
| `pub_actus-mercator/assets/js/scroll-effects.js` | 6162820 |    12 |   1 KB |  18 KB |

### HTML

| Archivo                                                                  | Inodo   | Links | Tamaño | Ahorro |
| ------------------------------------------------------------------------ | ------- | ----: | -----: | -----: |
| `pub_actus-mercator/assets/interactions.html`                            | 5639034 |    12 |   1 KB |  11 KB |
| `pub_actus-mercator/_partials/title-block-link-buttons/title-block.html` | 5640442 |    12 |   2 KB |  25 KB |

### YAML

| Archivo                                                   | Inodo   | Links | Tamaño | Ahorro |
| --------------------------------------------------------- | ------- | ----: | -----: | -----: |
| `pub_actus-mercator/inteligencia-comercial/_metadata.yml` | 5647618 |    37 |  15 KB | 571 KB |
| `website-achalma/blog/posts/_metadata.yml`                | 5637346 |     3 |  14 KB |  29 KB |
| `website-achalma/publication/_metadata.yml`               | 5637343 |     2 |  391 B |  391 B |

### Markdown

| Archivo                                    | Inodo   | Links | Tamaño | Ahorro |
| ------------------------------------------ | ------- | ----: | -----: | -----: |
| `pub_actus-mercator/assets/js/README.md`   | 6162822 |    12 |   2 KB |  23 KB |
| `pub_actus-mercator/assets/scss/README.md` | 6162826 |    12 |   6 KB |  66 KB |
| `pub_actus-mercator/docs/README.md`        | 5653394 |    12 |  14 KB | 164 KB |
| `pub_actus-mercator/SECURITY.md`           | 5640356 |    12 |  619 B |   6 KB |

### QMD

| Archivo                                    | Inodo   | Links | Tamaño | Ahorro |
| ------------------------------------------ | ------- | ----: | -----: | -----: |
| `pub_actus-mercator/404.qmd`               | 5640352 |    12 |  259 B |   2 KB |
| `pub_actus-mercator/_contenido-final.qmd`  | 5640357 |    13 |  106 B |   1 KB |
| `pub_actus-mercator/_contenido-inicio.qmd` | 5640358 |    13 |  197 B |   2 KB |

### Lua

| Archivo                                           | Inodo   | Links | Tamaño | Ahorro |
| ------------------------------------------------- | ------- | ----: | -----: | -----: |
| `pub_actus-mercator/_filters/apa-floats-html.lua` | 5653238 |    12 |   6 KB |  71 KB |
| `pub_actus-mercator/_filters/_metadata-pdf.lua`   | 5653239 |    12 |   1 KB |  13 KB |

### Scripts

| Archivo                                        | Inodo   | Links | Tamaño | Ahorro |
| ---------------------------------------------- | ------- | ----: | -----: | -----: |
| `pub_actus-mercator/scripts/build-page-css.sh` | 6162951 |    12 |   2 KB |  24 KB |

### Otros

| Archivo                                                | Inodo   | Links | Tamaño | Ahorro |
| ------------------------------------------------------ | ------- | ----: | -----: | -----: |
| `pub_actus-mercator/assets/css/components/bibbase.css` | 6162818 |    12 |   2 KB |  26 KB |
| `pub_actus-mercator/assets/css/pages/about.css`        | 6162817 |    12 |   2 KB |  30 KB |
| `pub_actus-mercator/assets/css/pages/contact.css`      | 6162816 |    12 |   2 KB |  29 KB |
| `pub_actus-mercator/assets/css/pages/home.css`         | 6162814 |    12 |   7 KB |  83 KB |
| `pub_actus-mercator/assets/css/pages/listing.css`      | 6162815 |    12 |   2 KB |  23 KB |
| `pub_actus-mercator/.gitignore`                        | 5640285 |    12 |   7 KB |  84 KB |
| `pub_actus-mercator/LICENSE`                           | 5640354 |    12 |  16 KB | 179 KB |

## Top archivos más compartidos

| Posición | Archivo                                                   | Links | Tamaño | Ahorro |
| -------: | --------------------------------------------------------- | ----: | -----: | -----: |
|        1 | `pub_actus-mercator/inteligencia-comercial/_metadata.yml` |    37 |  15 KB | 571 KB |
|        2 | `pub_actus-mercator/_contenido-final.qmd`                 |    13 |  106 B |   1 KB |
|        3 | `pub_actus-mercator/_contenido-inicio.qmd`                |    13 |  197 B |   2 KB |
|        4 | `pub_actus-mercator/404.qmd`                              |    12 |  259 B |   2 KB |
|        5 | `pub_actus-mercator/assets/css/components/bibbase.css`    |    12 |   2 KB |  26 KB |
|        6 | `pub_actus-mercator/assets/css/pages/about.css`           |    12 |   2 KB |  30 KB |
|        7 | `pub_actus-mercator/assets/css/pages/contact.css`         |    12 |   2 KB |  29 KB |
|        8 | `pub_actus-mercator/assets/css/pages/home.css`            |    12 |   7 KB |  83 KB |
|        9 | `pub_actus-mercator/assets/css/pages/listing.css`         |    12 |   2 KB |  23 KB |
|       10 | `pub_actus-mercator/assets/interactions.html`             |    12 |   1 KB |  11 KB |

## Archivos críticos

Archivos con **5 o más enlaces**: modificar su contenido afecta a todas sus copias.

| Archivo                                                                  | Inodo   | Links | Impacto de una modificación |
| ------------------------------------------------------------------------ | ------- | ----: | --------------------------- |
| `pub_actus-mercator/404.qmd`                                             | 5640352 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/css/components/bibbase.css`                   | 6162818 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/css/pages/about.css`                          | 6162817 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/css/pages/contact.css`                        | 6162816 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/css/pages/home.css`                           | 6162814 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/css/pages/listing.css`                        | 6162815 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/interactions.html`                            | 5639034 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/js/cursor.js`                                 | 6162819 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/js/hero.js`                                   | 6162821 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/js/navbar.js`                                 | 6162823 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/js/README.md`                                 | 6162822 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/js/scroll-effects.js`                         | 6162820 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/00-settings/_bootstrap.scss`             | 6162846 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/00-settings/_layout.scss`                | 6162845 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/00-settings/_palette-dark.scss`          | 6162850 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/00-settings/_palette-light.scss`         | 6162848 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/00-settings/_tokens-dark.scss`           | 6162847 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/00-settings/_tokens-light.scss`          | 6162849 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/00-settings/_typography.scss`            | 6162851 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/01-tools/_mixins.scss`                   | 6162840 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/02-base/_fonts.scss`                     | 6162828 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/02-base/_reset.scss`                     | 6162830 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/02-base/_root.scss`                      | 6162827 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/02-base/_typography.scss`                | 6162829 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/03-layout/_footer.scss`                  | 6162843 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/03-layout/_navbar.scss`                  | 6162844 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/03-layout/_responsive.scss`              | 6162841 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/03-layout/_toc.scss`                     | 6162842 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_buttons.scss`             | 6162860 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_callouts.scss`            | 6162861 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_citations.scss`           | 6162858 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_code.scss`                | 6162862 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_floats.scss`              | 6160717 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_listings.scss`            | 6162854 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_math.scss`                | 6162857 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_pagination.scss`          | 6162855 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_search.scss`              | 6162864 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_section-numbers.scss`     | 6162856 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_social.scss`              | 6162859 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_tables.scss`              | 6162853 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/04-components/_title-block.scss`         | 6162863 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/05-interactions/_microinteractions.scss` | 6162852 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/05-pages/about.scss`                     | 6162839 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/05-pages/_blog.scss`                     | 6162835 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/05-pages/contact.scss`                   | 6162836 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/05-pages/_courses.scss`                  | 6162837 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/05-pages/home.scss`                      | 6162833 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/05-pages/listing.scss`                   | 6162838 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/05-pages/_post.scss`                     | 6162831 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/05-pages/_projects.scss`                 | 6162834 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/05-pages/_publications.scss`             | 6162832 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/06-themes/_dark-adjustments.scss`        | 6162865 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/README.md`                               | 6162826 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/theme-dark.scss`                         | 6162824 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/assets/scss/theme-light.scss`                        | 6162825 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/_contenido-final.qmd`                                | 5640357 |    13 | Afecta a 13 ubicaciones     |
| `pub_actus-mercator/_contenido-inicio.qmd`                               | 5640358 |    13 | Afecta a 13 ubicaciones     |
| `pub_actus-mercator/docs/README.md`                                      | 5653394 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/_filters/apa-floats-html.lua`                        | 5653238 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/_filters/_metadata-pdf.lua`                          | 5653239 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/.gitignore`                                          | 5640285 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/inteligencia-comercial/_metadata.yml`                | 5647618 |    37 | Afecta a 37 ubicaciones     |
| `pub_actus-mercator/LICENSE`                                             | 5640354 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/_partials/title-block-link-buttons/title-block.html` | 5640442 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/scripts/build-page-css.sh`                           | 6162951 |    12 | Afecta a 12 ubicaciones     |
| `pub_actus-mercator/SECURITY.md`                                         | 5640356 |    12 | Afecta a 12 ubicaciones     |

## Resumen por directorios

| Proyecto                   | Archivos compartidos | Espacio ahorrado |
| -------------------------- | -------------------: | ---------------: |
| `pub_actus-mercator`       |                   67 |            15 KB |
| `pub_aequilibria`          |                   66 |              0 B |
| `pub_axiomata`             |                   67 |            15 KB |
| `pub_chaska`               |                   69 |            47 KB |
| `pub_dialectica-y-mercado` |                   66 |              0 B |
| `pub_epsilon-y-beta`       |                   75 |           142 KB |
| `pub_methodica`            |                   66 |              0 B |
| `pub_numerus-scriptum`     |                   76 |           158 KB |
| `pub_optimums`             |                   67 |            15 KB |
| `pub_pecunia-fluxus`       |                   67 |            15 KB |
| `pub_res-publica`          |                   66 |              0 B |
| `website-achalma`          |                   72 |            30 KB |

> El ahorro se atribuye al directorio donde existen copias duplicadas
> del mismo inodo (tamaño × copias adicionales dentro del directorio).

## Checklist de auditoría

- [x] Escaneo completado (68 conjunto(s) inventariado(s))
- [x] Todos los conjuntos están completos dentro del directorio analizado
- [x] Ningún conjunto con tamaño 0 bytes
- [ ] Comparado con la ejecución anterior: `git diff -- reports/hardlinks-report.md`
- [ ] Revisados los conjuntos marcados como «Parcial» (si existen)
- [ ] Verificado que los archivos críticos siguen sincronizados

## Comandos útiles

```bash
# Ver inodo, tamaño y número de enlaces de un archivo
stat -c '%i %s %h %n' archivo

# Localizar todos los enlaces de un inodo específico
find '/home/achalmaedison/Documents' -inum INODO

# Localizar todos los enlaces del mismo archivo físico
find '/home/achalmaedison/Documents' -samefile archivo

# Listar todos los archivos con más de un hard link
find '/home/achalmaedison/Documents' -type f -links +1
```

## Conclusión

El análisis identificó **68 conjunto(s)** de hard links que agrupan **824 archivo(s)**, con un ahorro total de **2 MB** en disco.

No se detectaron inconsistencias: el sistema de hard links se encuentra en buen estado.
