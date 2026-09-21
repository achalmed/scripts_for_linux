---
tipo: plan
titulo: "Visión de producto — Backup Studio (script_backup_suite) (2026-07-13)"
estado: hecho
creado: 2026-07-13
---
Este proyecto es diferente a los anteriores. Mientras que **Quarto Studio**, **Document Studio**, **Git Studio** y **Filesystem Studio** pueden convertirse en aplicaciones grandes con interfaz gráfica, **Backup Suite** no intentaría convertirlo en otra aplicación independiente. Lo convertiría en un **motor (engine)** reutilizable por toda la suite.

De hecho, creo que este proyecto es demasiado pequeño para vivir solo.

---

# Mi visión

> Visión de producto escrita en el vault el 2026-07-13 (`01 notes/proyecto-backup-studio.md`, tipo idea) y trasladada a `docs/` del repo en
> DOC8 (2026-09-20, decisión D15): es el documento fundacional de lo que hoy es Backup Studio (script_backup_suite). Lo construido y vigente está en
> `README.md` y `CLAUDE.md`; lo que aquí se prometió y no se hizo es historia, no pendiente.

No lo llamaría

> script_backup_suite

Lo llamaría

> **Backup Engine**

o

> **Backup Core**

Porque su función no debería ser únicamente ejecutar respaldos.

Debería ser **la infraestructura de respaldo de toda la plataforma**.

---

# ¿Qué debería respaldar?

Mucho más que copiar archivos.

Por ejemplo

```text
Workspace

↓

Proyectos

↓

Configuraciones

↓

Repositorios Git

↓

Bases de datos SQLite

↓

Plantillas

↓

Logs

↓

Preferencias

↓

Backups
```

Todos los Studios utilizarían el mismo motor.

---

# Yo lo dividiría

Actualmente

```text
analyzer.sh

processor.sh

summary.sh
```

Es demasiado genérico.

Lo organizaría algo así

```text
backup_engine/

core/

backup.sh

restore.sh

verify.sh

checksum.sh

incremental.sh

snapshot.sh

compression.sh

encryption.sh

scheduler.sh

retention.sh

report.sh
```

---

# Tipos de respaldo

No solo uno.

```text
Completo

Incremental

Diferencial

Snapshot

Mirror

Versionado
```

---

# Versionado

Muy importante.

Ejemplo

```text
Proyecto

↓

Backup 1

↓

Backup 2

↓

Backup 3

↓

Restaurar cualquiera
```

---

# Integridad

Nunca confiar solamente en rsync.

Siempre verificar.

```text
SHA256

↓

Comparar

↓

Reporte

↓

OK
```

---

# Políticas

Una sección

```text
Mantener

30 días

↓

Eliminar automáticamente
```

o

```text
Mantener

10 versiones
```

---

# Compresión

Elegir

```text
gzip

xz

zstd

bzip2

none
```

---

# Cifrado

Muy útil.

```text
AES

GPG

age
```

---

# Destinos

No solamente

```text
Disco externo
```

También

```text
USB

NAS

SSH

SFTP

WebDAV

Nube
```

---

# Programador

Algo parecido a cron.

```text
Cada hora

Cada día

Cada semana

Cada mes
```

---

# Reportes

Generar

```text
Markdown

PDF

HTML

JSON
```

---

# Restauración

No solo

```text
Restore
```

Sino

```text
Restaurar

↓

Archivo

↓

Carpeta

↓

Proyecto

↓

Workspace
```

---

# Integración con Git

Antes del backup.

```text
Git Status

↓

Commit opcional

↓

Backup
```

---

# Integración con Filesystem Studio

Filesystem detecta

↓

Archivos nuevos

↓

Backup Engine

↓

Respaldo automático

---

# Integración con Document Studio

Cuando conviertes

```text
DOCX

↓

Markdown
```

Guardar automáticamente una copia del original.

---

# Integración con Quarto Studio

Antes de renderizar.

```text
Backup

↓

Render

↓

Deploy
```

---

# Integración con Academic Studio

Antes de modificar una tesis.

↓

Crear Snapshot.

---

# Arquitectura

Yo haría

```text
Backup Engine
│
├── Scanner
├── Snapshot Manager
├── Restore Manager
├── Integrity Checker
├── Compression
├── Encryption
├── Scheduler
├── Retention Manager
├── Reports
└── API
```

---

# La idea más interesante

Aquí veo una oportunidad enorme.

En lugar de tener

```text
Filesystem Studio

Git Studio

Document Studio

Quarto Studio

Backup Suite
```

Yo tendría una arquitectura por capas.

```text
Studio Platform
│
├── Engines
│
│   ├── Backup Engine
│   ├── Git Engine
│   ├── Filesystem Engine
│   ├── Document Engine
│   ├── Quarto Engine
│   ├── PDF Engine
│   ├── OCR Engine
│   └── AI Engine
│
├── Studio Core
│
├── Plugins
│
└── Applications
    ├── Filesystem Studio
    ├── Git Studio
    ├── Document Studio
    ├── Quarto Studio
    └── Academic Studio
```

De esa forma, los "Studios" son solo interfaces de usuario, mientras que toda la lógica vive en motores reutilizables.

## Mi recomendación más importante

Después de ver los cinco proyectos que has compartido, creo que el siguiente paso no es seguir creando más aplicaciones, sino **extraer la infraestructura común**. Muchas capacidades (registro de eventos, consola, tareas, configuración, escaneo, reportes, respaldo) aparecen repetidas una y otra vez.

Yo dedicaría un ciclo de desarrollo completo a construir una **Studio Platform** con tres niveles claramente definidos:

- **Core**: interfaz, tareas, configuración, base de datos, plugins y eventos.

- **Engines**: Git, Filesystem, Backup, Documentos, Quarto, PDF, OCR, etc.

- **Studios**: aplicaciones especializadas que combinan esos motores según su propósito.

Con esa separación, `script_backup_suite` dejaría de ser un script aislado y se convertiría en un componente fundamental que cualquier otra aplicación de la plataforma puede invocar para crear puntos de restauración, proteger datos y automatizar respaldos de forma consistente. Esa arquitectura será mucho más sostenible si tu objetivo es desarrollar un ecosistema completo de herramientas para Linux y para tu trabajo académico.
