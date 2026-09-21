---
tipo: doc
titulo: "Visión de producto — Filesystem Studio (2026-07-13)"
estado: hecho
creado: 2026-07-13
---
De los cuatro proyectos que me has mostrado (**Quarto Studio, Document Studio, Git Studio y Filesystem Studio**), este es el que tiene **mayor potencial técnico**, pero también el que corre más riesgo de quedarse como una colección de utilidades si no defines una visión más amplia.

Creo que el nombre **Filesystem Studio** incluso se queda corto. Lo que realmente estás construyendo podría ser un **administrador avanzado del sistema de archivos**, algo situado entre un explorador de archivos, un analizador de discos y una plataforma de automatización.

---

# Mi visión

> Visión de producto escrita en el vault el 2026-07-13 (`01 notes/proyecto-filesystem-studio.md`, tipo idea) y trasladada a `docs/` del repo en
> DOC8 (2026-09-20, decisión D15): es el documento fundacional de lo que hoy es Filesystem Studio. Lo construido y vigente está en
> `README.md` y `CLAUDE.md`; lo que aquí se prometió y no se hizo es historia, no pendiente.

No lo pensaría como

> "una GUI para scripts"

Lo pensaría como

> **Filesystem Studio**
> 
> *An Advanced Filesystem Analysis & Automation Platform*

Es decir, una plataforma para **analizar, organizar, automatizar y mantener sistemas de archivos**.

---

# Lo primero que cambiaría

Actualmente tienes

```text
Folders

Tree

Hardlinks

Stats
```

Eso son funcionalidades.

Pero al usuario le interesa otra cosa.

Le interesa responder preguntas como

> ¿Qué está ocupando mi disco?

> ¿Dónde hay archivos duplicados?

> ¿Qué carpetas crecieron esta semana?

> ¿Qué puedo eliminar?

> ¿Qué puedo respaldar?

---

# Cambiar el concepto

En lugar de páginas

```text
Tree

Stats

Folders
```

Yo tendría módulos.

```text
Explorer

Analysis

Maintenance

Automation

Reports
```

Mucho más natural.

---

# Dashboard

No un panel vacío.

Un dashboard del disco.

Ejemplo

```text
Discos

3

Espacio usado

812 GB

Archivos

1 243 118

Carpetas

98 221

Duplicados

23 GB

Hardlinks

11 204

Enlaces rotos

24

Archivos grandes

412
```

---

# Explorer

No un QFileSystemModel.

Sino un explorador inteligente.

Ejemplo

```text
Documentos

Imágenes

Vídeos

Audio

Código

Proyectos

Archivos grandes

Recientes

Duplicados

Sin extensión
```

---

# Scanner

Aquí invertiría muchísimo.

No un scanner simple.

Un motor.

```text
Filesystem Scanner

↓

Metadata

↓

Hashes

↓

Permisos

↓

Hardlinks

↓

Mime

↓

Owner

↓

ACL

↓

Extended Attributes

↓

Git

↓

Report
```

---

# Base de datos

Aquí sí usaría SQLite.

Después de escanear.

```text
Filesystem.db

Files

Folders

Extensions

Hashes

Links

History

Reports
```

No volver a recorrer el disco para cada consulta.

---

# Historial

Esto sería enorme.

Escaneo hoy.

↓

Escaneo mañana.

↓

Comparar.

```text
+324 archivos

-22 archivos

+3.2 GB

12 archivos renombrados
```

---

# Timeline

Mostrar

```text
Hoy

Ayer

Semana

Mes
```

Qué cambió.

---

# Duplicados

No solamente hardlinks.

También

```text
Duplicados exactos

Duplicados parciales

Archivos similares

Imágenes similares

Videos similares
```

---

# Organización automática

Algo tipo

```text
Downloads

↓

Organizar

↓

PDF

↓

Documentos

↓

Imágenes

↓

ZIP

↓

Código

↓

Otros
```

---

# Rules Engine

Muy potente.

Ejemplo

```text
Si

extensión=pdf

y

tamaño>100MB

↓

Mover

↓

/Documentos/Grandes
```

Como un sistema de automatización.

---

# Watch Mode

Ya tienes workers.

Yo agregaría

```text
Watch

↓

Nueva carpeta

↓

Escanear

↓

Actualizar índice

↓

Actualizar dashboard
```

---

# Visualización

Muy importante.

Gráficos.

Por ejemplo

```text
Extensiones

↓

Pie Chart
```

```text
Espacio

↓

Treemap
```

```text
Carpetas

↓

Sunburst
```

```text
Archivos

↓

Timeline
```

---

# Buscador

No buscar por nombre.

Buscar por propiedades.

```text
size>100MB

owner=edison

ext=pdf

created<2023

hash=...
```

---

# Integración Git

Detectar automáticamente.

```text
Proyecto Git

↓

Mostrar branch

↓

Estado

↓

Último commit
```

---

# Integración Quarto

Detectar

```text
_quarto.yml

↓

Proyecto Quarto
```

---

# Integración LaTeX

Detectar

```text
.tex

↓

Proyecto LaTeX
```

---

# Integración Python

Detectar

```text
pyproject.toml

↓

Proyecto Python
```

---

# Project Detection

Esto sería buenísimo.

Escanea.

↓

Detecta automáticamente.

```text
Proyecto Python

Proyecto Rust

Proyecto Go

Proyecto Quarto

Proyecto Hugo

Proyecto LaTeX

Proyecto React

Proyecto Vue
```

---

# Metadata

Cada archivo tendría

```text
Tipo

Hash

Mime

Extensión

Fecha

Owner

Grupo

ACL

Git

Proyecto
```

---

# Reportes

No solamente Markdown.

También

```text
PDF

CSV

JSON

SQLite

Excel

HTML
```

---

# Automatización

Una sección completa.

```text
Tareas

↓

Escanear

↓

Respaldar

↓

Organizar

↓

Eliminar temporales

↓

Buscar duplicados

↓

Actualizar índices
```

---

# API

Todo debería poder ejecutarse.

```python
Filesystem.scan()

Filesystem.stats()

Filesystem.tree()

Filesystem.export()

Filesystem.links()

Filesystem.clean()
```

---

# Lo más importante: unificar los cuatro proyectos

Aquí es donde veo el verdadero potencial.

Tienes:

- Filesystem Studio

- Git Studio

- Document Studio

- Quarto Studio

Pero en realidad los cuatro trabajan sobre el mismo concepto:

```text
Proyecto

↓

Archivos

↓

Metadatos

↓

Procesamiento

↓

Reportes
```

Por eso, en lugar de mantener cuatro aplicaciones completamente independientes, construiría una **plataforma común**.

## Propuesta: Studio Platform

```text
Studio Platform
│
├── Studio Core
│   ├── Workspace Manager
│   ├── File Explorer
│   ├── Task Manager
│   ├── Plugin Manager
│   ├── Event Bus
│   ├── Command Bus
│   ├── Logger
│   ├── Console
│   ├── Settings
│   ├── Search Engine
│   ├── Database
│   └── AI Services
│
├── Filesystem Studio
├── Git Studio
├── Document Studio
├── Quarto Studio
├── LaTeX Studio
├── Academic Studio
└── Data Studio
```

Cada "Studio" sería simplemente un conjunto de módulos especializados que reutilizan el mismo núcleo.

## Mi prioridad de desarrollo

Si tuviera que planificar este ecosistema, no desarrollaría los cuatro estudios al mismo tiempo. El orden que considero más sólido es:

1. **Studio Core**: infraestructura compartida (ventanas, tareas, configuración, plugins, explorador, consola, base de datos, eventos).

2. **Filesystem Studio**: porque proporciona las capacidades de exploración, indexación y análisis que pueden aprovechar los demás.

3. **Git Studio**: para gestionar el ciclo de vida y la sincronización de todos los proyectos.

4. **Document Studio**: para la conversión y el procesamiento documental.

5. **Quarto Studio**: construido sobre las capacidades anteriores para la gestión y publicación de contenidos.

Con esta estrategia, cada nuevo estudio añade funcionalidades sobre una base consolidada en lugar de duplicar componentes. A largo plazo tendrás una suite coherente, más fácil de mantener y mucho más escalable que un conjunto de aplicaciones desarrolladas de forma independiente.
