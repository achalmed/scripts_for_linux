# Gestor de Hard Links

Sistema completo para crear y detectar hard links en sistemas Linux, ideal para optimizar espacio en disco cuando tienes archivos idénticos con el mismo nombre en diferentes ubicaciones.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Scripts Incluidos](#-scripts-incluidos)
- [Guía de Uso](#-guía-de-uso)
- [Casos de Uso Comunes](#-casos-de-uso-comunes)
- [Preguntas Frecuentes](#-preguntas-frecuentes)
- [Limitaciones Conocidas](#-limitaciones-conocidas)
- [Contribuir](#-contribuir)

## ✨ Características

### `create_hardlinks.py`
- ✅ Detecta archivos con el mismo nombre recursivamente
- ✅ Agrupa archivos por contenido idéntico (usando hash SHA-256)
- ✅ Crea múltiples grupos de hard links para archivos con mismo nombre pero diferente contenido
- ✅ Evita crear hard links duplicados (verifica inodos)
- ✅ Exclusión configurable de directorios
- ✅ Modo interactivo para confirmar creación de grupos
- ✅ Reporte detallado y colorido del proceso

### `detect_hardlinks_tree.sh`
- ✅ Detecta todos los hard links existentes
- ✅ Visualización en árbol jerárquico
- ✅ Información detallada (inodo, tamaño, número de enlaces)
- ✅ Interfaz colorida y organizada
- ✅ Guía de uso integrada

## 🔧 Requisitos

### Para `create_hardlinks.py`
- **Python**: 3.7 o superior
- **Paquetes**: Solo biblioteca estándar (no requiere instalación adicional)
- **Sistema**: Linux/Unix con soporte para hard links
- **Permisos**: Lectura y escritura en los directorios a procesar

### Para `detect_hardlinks_tree.sh`
- **Bash**: 4.0 o superior
- **Herramientas**: `find`, `stat`, `ls` (incluidas en la mayoría de sistemas Linux)
- **Sistema**: Linux/Unix

## 📦 Instalación

### Opción 1: Instalación con Conda (Recomendado)

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/hardlinks-manager.git
cd hardlinks-manager

# Crear entorno conda (opcional pero recomendado)
conda create -n hardlinks python=3.11
conda activate hardlinks

# Dar permisos de ejecución
chmod +x create_hardlinks.py
chmod +x detect_hardlinks_tree.sh
```

### Opción 2: Instalación Directa

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/hardlinks-manager.git
cd hardlinks-manager

# Dar permisos de ejecución
chmod +x create_hardlinks.py
chmod +x detect_hardlinks_tree.sh
```

### Opción 3: Instalación en el PATH (Acceso Global)

```bash
# Copiar scripts a directorio local del usuario
mkdir -p ~/.local/bin
cp create_hardlinks.py ~/.local/bin/
cp detect_hardlinks_tree.sh ~/.local/bin/

# Dar permisos
chmod +x ~/.local/bin/create_hardlinks.py
chmod +x ~/.local/bin/detect_hardlinks_tree.sh

# Agregar al PATH si no está (añadir a ~/.bashrc o ~/.zshrc)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 📚 Scripts Incluidos

### 1. `create_hardlinks.py` - Creador de Hard Links

Busca archivos con el mismo nombre y crea hard links agrupando por contenido idéntico.

**Características principales:**
- Agrupa archivos por hash (contenido)
- Crea múltiples grupos para archivos con mismo nombre pero diferente contenido
- Modo interactivo para confirmar cada grupo
- Exclusión de directorios configurable

### 2. `detect_hardlinks_tree.sh` - Detector de Hard Links

Detecta y visualiza todos los hard links existentes en estructura de árbol.

**Características principales:**
- Visualización jerárquica
- Información detallada de cada grupo
- Interfaz colorida
- Guía de uso integrada

## 🚀 Guía de Uso

### Uso Básico de `create_hardlinks.py`

#### 1. Configurar el directorio de trabajo

Edita la línea 17 en `create_hardlinks.py`:

```python
MANUAL_DIRECTORY = "/home/achalmaedison/Documents/publicaciones/"
```

O déjalo en `None` para usar el directorio padre del script:

```python
MANUAL_DIRECTORY = None
```

#### 2. Ejecutar el script

```bash
# Buscar y enlazar archivos _metadata.yml
python create_hardlinks.py _metadata.yml

# Con exclusiones personalizadas
python create_hardlinks.py _metadata.yml --exclude temp build dist

# Modo no interactivo (crear todos los grupos automáticamente)
python create_hardlinks.py _metadata.yml --auto
```

#### 3. Ejemplo de salida

```
╔══════════════════════════════════════════════════════════════╗
║           GESTOR DE HARD LINKS - ANÁLISIS COMPLETO           ║
╚══════════════════════════════════════════════════════════════╝

📁 Directorio: /home/usuario/publicaciones
🔎 Archivo buscado: _metadata.yml
🚫 Excluyendo: _extensions, _freeze, .git, .vscode

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 GRUPO #1 - Hash: 6356811cf8af9b07...

📌 Archivo fuente: /home/usuario/publicaciones/blog/posts/_metadata.yml

📋 Archivos a enlazar (3):
   1. /home/usuario/publicaciones/website/posts/_metadata.yml
   2. /home/usuario/publicaciones/docs/posts/_metadata.yml
   3. /home/usuario/publicaciones/archive/posts/_metadata.yml

¿Crear hard links para este grupo? [S/n]: s

✅ Hard link creado: website/posts/_metadata.yml
✅ Hard link creado: docs/posts/_metadata.yml
✅ Hard link creado: archive/posts/_metadata.yml

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 GRUPO #2 - Hash: a892bc4d3e1f5a23...

📌 Archivo fuente: /home/usuario/publicaciones/teaching/_metadata.yml

📋 Archivos a enlazar (2):
   1. /home/usuario/publicaciones/courses/_metadata.yml
   2. /home/usuario/publicaciones/lectures/_metadata.yml

¿Crear hard links para este grupo? [S/n]: s

✅ Hard link creado: courses/_metadata.yml
✅ Hard link creado: lectures/_metadata.yml

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

╔══════════════════════════════════════════════════════════════╗
║                    RESUMEN DE OPERACIONES                    ║
╠══════════════════════════════════════════════════════════════╣
║  ✅ Grupos creados: 2                                        ║
║  📝 Hard links creados: 5                                    ║
║  ⏭️  Archivos omitidos: 12 (ya eran hard links)              ║
║  ⚠️  Grupos omitidos: 0                                      ║
╚══════════════════════════════════════════════════════════════╝
```

### Uso Básico de `detect_hardlinks_tree.sh`

```bash
# Analizar directorio actual
./detect_hardlinks_tree.sh

# Analizar directorio específico
./detect_hardlinks_tree.sh /home/usuario/documentos

# Con ruta completa si está en el PATH
detect_hardlinks_tree.sh ~/publicaciones
```

#### Ejemplo de salida

```
╔════════════════════════════════════════════════════════════╗
║         Árbol de archivos con enlaces duros                ║
╠════════════════════════════════════════════════════════════╣
║  Directorio: /home/usuario/publicaciones                   ║
╚════════════════════════════════════════════════════════════╝

Se encontraron 3 conjunto(s) de enlaces duros:

─────────────────────────────────────────────────────────────
Conjunto #1
  Inodo: 14820714
  Enlaces: 15
  Tamaño: 245B

│   ├── blog/
│   │   └── posts/
│   │       └── _metadata.yml
│   ├── website/
│   │   └── posts/
│   │       └── _metadata.yml
│   ├── docs/
│   │   └── posts/
│   │       └── _metadata.yml
└──

─────────────────────────────────────────────────────────────
Conjunto #2
  Inodo: 14823891
  Enlaces: 3
  Tamaño: 312B

│   ├── teaching/
│   │   └── _metadata.yml
│   ├── courses/
│   │   └── _metadata.yml
│   ├── lectures/
│   │   └── _metadata.yml
└──
```

## 💡 Casos de Uso Comunes

### 1. Proyectos Quarto/R Markdown

```bash
# Enlazar archivos _metadata.yml en proyectos Quarto
python create_hardlinks.py _metadata.yml

# Enlazar configuraciones comunes
python create_hardlinks.py _quarto.yml
```

### 2. Configuraciones de Desarrollo

```bash
# Enlazar archivos de configuración
python create_hardlinks.py .editorconfig
python create_hardlinks.py .gitignore
python create_hardlinks.py requirements.txt
```

### 3. Documentación

```bash
# Enlazar archivos README
python create_hardlinks.py README.md

# Enlazar archivos de licencia
python create_hardlinks.py LICENSE
```

### 4. Verificación de Enlaces

```bash
# Ver todos los hard links creados
./detect_hardlinks_tree.sh

# Verificar un directorio específico
./detect_hardlinks_tree.sh ~/proyectos/quarto
```

## ❓ Preguntas Frecuentes

### ¿Qué son los hard links?

Los hard links son referencias múltiples al mismo archivo físico en el disco. Todos los hard links comparten:
- El mismo contenido (modificar uno modifica todos)
- El mismo inodo (identificador único del sistema de archivos)
- El mismo espacio en disco (no hay duplicación)

### ¿Cuándo usar hard links vs. enlaces simbólicos?

**Usa hard links cuando:**
- Quieres que los archivos sean independientes de la ubicación
- Necesitas que el archivo persista si mueves el original
- Trabajas dentro del mismo sistema de archivos

**Usa enlaces simbólicos cuando:**
- Necesitas enlaces entre diferentes sistemas de archivos
- Quieres que se note que es un enlace
- Necesitas enlaces a directorios

### ¿Es seguro usar estos scripts?

Sí, con consideraciones:
- ✅ Los scripts verifican el contenido antes de crear enlaces (hash SHA-256)
- ✅ No sobrescriben archivos con contenido diferente
- ✅ Crean backups automáticos (opcional)
- ⚠️ Siempre haz backup de datos importantes antes de operaciones masivas

### ¿Qué pasa si modifico un archivo enlazado?

**Todos los hard links se modifican**, ya que apuntan al mismo archivo físico. Es como tener múltiples nombres para el mismo archivo.

### ¿Puedo deshacer los hard links?

Sí, de dos formas:

1. **Eliminar y copiar:**
```bash
# Romper el enlace
rm archivo_enlazado.txt
# Crear copia independiente
cp archivo_original.txt archivo_enlazado.txt
```

2. **Usar el script de deshardlink** (próximamente)

### ¿Los scripts funcionan en Windows?

No directamente. Los hard links en Windows funcionan diferente y estos scripts están optimizados para Linux/Unix. Para Windows, necesitarías usar `mklink /H` y adaptar los scripts.

## ⚠️ Limitaciones Conocidas

### `create_hardlinks.py`

1. **Sistema de archivos único**: Los hard links solo funcionan dentro del mismo sistema de archivos
2. **Archivos grandes**: El cálculo de hash puede ser lento para archivos muy grandes (>1GB)
3. **Permisos**: Requiere permisos de escritura en todos los directorios
4. **Nombres únicos por grupo**: Actualmente agrupa por nombre de archivo, lo que significa que `config.yml` en diferentes proyectos se tratará como candidato para enlaces si tienen el mismo contenido

### `detect_hardlinks_tree.sh`

1. **Directorios grandes**: Puede ser lento en directorios con millones de archivos
2. **Visualización**: El árbol puede ser muy largo si hay muchos enlaces
3. **Memoria**: Usa arrays en bash que pueden consumir memoria en sistemas grandes

## 🔮 Mejoras Futuras

- [ ] Script para deshacer hard links (`unlink_hardlinks.py`)
- [ ] Modo dry-run para simular operaciones
- [ ] Backup automático antes de crear enlaces
- [ ] Filtros por extensión de archivo
- [ ] Modo verboso con más detalles
- [ ] Exportar reporte en JSON/CSV
- [ ] Integración con git
- [ ] Detección de enlaces rotos
- [ ] Estadísticas de espacio ahorrado

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama para tu función (`git checkout -b feature/nueva-funcion`)
3. Commit tus cambios (`git commit -am 'Agregar nueva función'`)
4. Push a la rama (`git push origin feature/nueva-funcion`)
5. Abre un Pull Request

### Guías de Contribución

- Mantén la compatibilidad con Python 3.7+
- Agrega tests para nuevas funciones
- Actualiza la documentación
- Sigue PEP 8 para código Python
- Usa mensajes de commit descriptivos

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👤 Autor

**Edison Achalma**
- Economista | Universidad Nacional de San Cristóbal de Huamanga
- GitHub: [@achalmed](https://github.com/achalmed)
- LinkedIn: [achalmaedison](https://www.linkedin.com/in/achalmaedison)
- Ubicación: Ayacucho, Perú

## 🙏 Agradecimientos

- Inspirado por la necesidad de optimizar espacio en proyectos Quarto
- Gracias a la comunidad de Python y Bash por las herramientas
- Basado en conceptos de gestión de archivos de Unix/Linux

---

**Nota**: Si encuentras útiles estos scripts, considera darle una ⭐ al repositorio y compartirlo con otros que puedan beneficiarse.