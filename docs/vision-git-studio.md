---
tipo: plan
titulo: "Visión de producto — Git Studio (2026-07-20)"
estado: hecho
creado: 2026-07-20
---
Creo que aquí hay una oportunidad mucho mayor de la que parece. En realidad **Git Studio no debería ser una aplicación de Git**, porque ya existen herramientas excelentes como GitKraken, Sourcetree, GitHub Desktop o incluso la integración de VS Code.

Lo que sí puedes hacer es construir una herramienta especializada para un problema que esas aplicaciones no resuelven bien: **administrar decenas o cientos de repositorios simultáneamente**.

Por lo que conozco de tus proyectos, tú tienes muchos repositorios (frameworks, scripts Linux, Quarto, LaTeX, cursos, tesis, web personal, etc.). Tu necesidad no es hacer un `git commit`; tu necesidad es saber **qué está pasando en todos tus repositorios al mismo tiempo**.

Ese debería ser el objetivo del proyecto.

---

# Yo cambiaría completamente el enfoque

> Visión de producto escrita en el vault el 2026-07-20 (`01 notes/proyecto-git-studio.md`, tipo idea) y trasladada a `docs/` del repo en
> DOC8 (2026-09-20, decisión D15): es el documento fundacional de lo que hoy es Git Studio. Lo construido y vigente está en
> `README.md` y `CLAUDE.md`; lo que aquí se prometió y no se hizo es historia, no pendiente.

En vez de

> Git Studio

Lo vería como

> **Repository Studio**

o incluso

> **Workspace Manager**

Porque Git es solo una parte.

---

# Lo que falta

Actualmente veo

```text
Clone

Sync

Reports

Repos
```

Eso está bien.

Pero para un usuario con muchos repositorios falta muchísimo.

---

# Dashboard global

No un dashboard del programa.

Un dashboard de TODOS los repositorios.

Ejemplo

```text
128 repositorios

117 sincronizados

4 con cambios

3 con conflictos

2 sin remote

7 ramas diferentes

12 pull pendientes

5 push pendientes
```

Eso es muchísimo más útil.

---

# Workspace

Yo agregaría

```text
Workspace

↓

Research

↓

Teaching

↓

Frameworks

↓

Linux

↓

Website

↓

Python

↓

Rust
```

Cada Workspace contiene muchos repositorios.

---

# Organización

Ejemplo

```text
Academic

├── thesis-framework

├── article-framework

├── quarto-studio

├── document-studio

Linux

├── scripts-linux

├── filesystem-studio

├── git-studio

Programming

├── python-utils

├── rust-utils
```

---

# Scanner automático

Escanea

```text
~/Documents

~/Projects

~/GitHub
```

Encuentra automáticamente

```text
.git
```

No hace falta agregarlos manualmente.

---

# Estado de cada repositorio

Una tabla tipo

| Repo          | Branch | Ahead | Behind | Dirty | Último Commit   |
| ------------- | ------ | ----- | ------ | ----- | --------------- |
| Quarto Studio | main   | 0     | 0      | ✔     | hace 3 horas    |
| Thesis        | dev    | 2     | 1      | ✔     | hace 1 día      |
| Website       | main   | 0     | 0      | ✘     | hace 10 minutos |

Eso sería fantástico.

---

# Commit Dashboard

Mostrar

```text
Hoy

17 commits

Esta semana

89 commits

Este mes

312 commits
```

Y gráficos.

---

# Historial

No solo Git log.

Sino

```text
Actividad

Últimos commits

Archivos modificados

Lenguajes

Contribución
```

---

# Batch Operations

Aquí está el gran potencial.

Selecciono

```text
120 repositorios
```

↓

Actualizar

↓

Fetch

↓

Pull

↓

Push

↓

Garbage Collect

↓

Prune

↓

Done

Todo automáticamente.

---

# Git Doctor

Algo parecido a

```bash
doctor
```

Que detecte

```text
HEAD corrupto

Remote inexistente

Conflictos

Repositorios huérfanos

Objetos dañados

Hooks rotos
```

---

# Git Analytics

Muy interesante.

Por ejemplo

```text
Commits por día

Commits por proyecto

Lenguajes

Autores

Líneas agregadas

Líneas eliminadas
```

---

# Git Backup

Algo que nadie hace.

Respaldar

```text
Configuración

Hooks

Branches

Tags

Config

Remotes
```

---

# Git Hooks Manager

Una GUI para

```text
pre-commit

pre-push

post-merge

post-checkout
```

Sin editar Bash.

---

# Release Manager

Ver

```text
Tags

Releases

Versiones

Changelog
```

---

# GitHub Integration

Aquí iría mucho más allá.

Mostrar

```text
Issues

PR

Actions

Releases

Stars

Forks

Watchers
```

Dentro del programa.

---

# Dependencias

Detectar

```text
README

LICENSE

.gitignore

CHANGELOG

CONTRIBUTING

CODEOWNERS
```

Y sugerir qué falta.

---

# Visualización

Una vista tipo mapa.

```text
Workspace

↓

Repo

↓

Branch

↓

Commit
```

Con grafos.

---

# Templates

Crear automáticamente

```text
Nuevo proyecto Python

Nuevo proyecto Rust

Nuevo proyecto Bash

Nuevo proyecto Quarto

Nuevo proyecto LaTeX
```

Con Git inicializado.

---

# Sincronización inteligente

En lugar de

```bash
git pull
```

Que haga

```text
Fetch

↓

Comparar

↓

Verificar conflictos

↓

Guardar stash

↓

Pull

↓

Restaurar stash

↓

Reportar
```

Muchísimo más seguro.

---

# Integración con tus otros proyectos

Aquí es donde veo el mayor potencial.

## Quarto Studio

Podría mostrar

```text
Estado Git

↓

Desde la barra lateral.
```

---

## Document Studio

Guardar automáticamente

```text
Versiones

↓

Git
```

---

## Academic Studio

Versionar

```text
Tesis

Artículos

Libros
```

---

# Arquitectura común

Aquí es donde veo una gran oportunidad.

Los tres proyectos que me mostraste (**Quarto Studio**, **Document Studio** y **Git Studio**) comparten casi la misma estructura:

- `services`
- `controllers`
- `workers`
- `resources`
- `widgets`
- `themes`
- `console`
- `tasks`

Eso me dice que en realidad estás desarrollando **la misma aplicación tres veces**.

En lugar de eso, yo construiría un **Studio Core** compartido:

```text
Studio Core
│
├── UI Framework
├── Task Manager
├── Plugin Manager
├── Event Bus
├── Command Bus
├── Console
├── Logger
├── Settings
├── Workspace Manager
├── File Explorer
└── Theme Engine
```

Y luego cada aplicación sería solo un conjunto de módulos:

```text
Studio Core
│
├── Git Plugin
├── Quarto Plugin
├── Documents Plugin
├── LaTeX Plugin
├── Academic Plugin
├── OCR Plugin
├── PDF Plugin
└── AI Plugin
```

## Mi recomendación principal

De los tres proyectos que has mostrado, no intentaría hacer tres aplicaciones independientes. Invertiría primero en un **núcleo compartido** (por ejemplo, `Studio Core`) que resuelva la infraestructura común: ventanas, explorador, consola, tareas, plugins, configuración, temas, registro de eventos y servicios base.

Una vez que ese núcleo exista, **Git Studio**, **Quarto Studio** y **Document Studio** pasarían a ser aplicaciones muy pequeñas construidas sobre la misma plataforma, compartiendo entre el 70 % y el 80 % del código. Eso reducirá el mantenimiento, facilitará añadir nuevas funciones y te permitirá crear una suite coherente de herramientas en lugar de varios proyectos que evolucionan por separado. Creo que esa arquitectura es la que mejor se adapta a tu objetivo de largo plazo de desarrollar un ecosistema completo para investigación, publicación, docencia y gestión de proyectos.
