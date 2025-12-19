# Ejemplos Prácticos de Uso

Este archivo contiene ejemplos reales de cómo usar los scripts en diferentes situaciones.

## 📋 Tabla de Contenidos

1. [Flujo de Trabajo Diario](#flujo-de-trabajo-diario)
2. [Actualización de Archivos Enlazados](#actualización-de-archivos-enlazados)
3. [Actualización Masiva de Índices](#actualización-masiva-de-índices)
4. [Trabajo con Ramas](#trabajo-con-ramas)
5. [Resolución de Conflictos](#resolución-de-conflictos)
6. [Automatización con Hooks](#automatización-con-hooks)
7. [Scripts Personalizados](#scripts-personalizados)

---

## Flujo de Trabajo Diario

### Escenario: Fin del día de trabajo

```bash
# 1. Verificar qué cambió en todos los repos
./repo-status.sh

# 2. Si hay cambios, sincronizar todos
./quick-sync.sh "update: cambios del $(date +%Y-%m-%d)"

# 3. Verificar que todo se subió correctamente
./repo-status.sh
```

### Escenario: Inicio del día

```bash
# Actualizar todos los repos antes de trabajar
cd ~/Projects
for repo in */; do 
    echo "Actualizando $repo..."
    cd "$repo" 
    git pull 
    cd ..
done

# O con un one-liner
cd ~/Projects && for d in */; do (cd "$d" && git pull); done
```

---

## Actualización de Archivos Enlazados

### Escenario: Modificaste _metadata.yml (archivo de enlace duro)

Como `_metadata.yml` es un enlace duro, el cambio se refleja automáticamente en todos los repos.

```bash
# Verificar qué repos se afectaron
./sync-repos.sh -c

# Sincronizar todos con mensaje específico
./sync-repos.sh -m "feat(config): actualizar metadata global - nuevo tema"

# O usar el script Python con auto-detección
./sync-repos.py -v  # Detectará automáticamente que es un cambio de metadata
```

### Escenario: Otros archivos compartidos (themes, CSS, etc.)

```bash
# Si modificaste archivos de tema
./sync-repos.sh -m "style: actualizar estilos globales"

# Si modificaste configuración de Quarto
./sync-repos.sh -m "feat(config): actualizar _quarto.yml"
```

---

## Actualización Masiva de Índices

### Escenario: Script Python regeneró todos los index.qmd

```bash
# Primero, ejecutar tu script de generación de índices
cd ~/Projects
python3 generar_indices.py  # O como se llame tu script

# Luego sincronizar con mensaje apropiado
cd ~/bin/git-sync
./sync-repos.py -m "docs: regenerar índices automáticos"

# O si quieres ser más específico
./sync-repos.sh -m "docs: actualizar índices generados por script - $(date +%Y-%m-%d)"
```

### Escenario: Actualizar solo algunos blogs

```bash
# Solo blogs de economía
./sync-repos.sh \
    -r "pecunia-fluxus,epsilon-y-beta,optimums" \
    -m "docs: actualizar índices económicos Q4-2025"

# Solo blogs de filosofía
./sync-repos.sh \
    -r "axiomata,dialectica-y-mercado,res-publica" \
    -m "docs: actualizar índices filosóficos"
```

---

## Trabajo con Ramas

### Escenario: Trabajando en rama de desarrollo

```bash
# Crear rama en todos los repos
cd ~/Projects
for repo in axiomata chaska methodica; do
    cd "$repo"
    git checkout -b feature/nuevo-diseño
    cd ..
done

# Hacer cambios...

# Sincronizar rama de desarrollo
# (Modificar repos-config.yml temporalmente o usar git directo)
cd ~/Projects/axiomata
git add -A
git commit -m "feat: nuevo diseño de header"
git push -u origin feature/nuevo-diseño

# Repetir para otros repos...
```

### Escenario: Merge y sincronización

```bash
# Después de hacer merge en GitHub, actualizar local
cd ~/Projects
for repo in */; do
    cd "$repo"
    git checkout main
    git pull
    cd ..
done
```

---

## Resolución de Conflictos

### Escenario: Conflictos después de pull

```bash
# Si quick-sync.sh falla
./repo-status.sh  # Ver qué repo tiene conflictos

# Resolver manualmente
cd ~/Projects/axiomata
git status
# Editar archivos conflictivos
git add .
git commit -m "fix: resolver conflictos de merge"
git push

# Luego continuar con los demás
./quick-sync.sh
```

### Escenario: Force push necesario (¡CUIDADO!)

```bash
# Solo si estás seguro y es tu propio repo
cd ~/Projects/repo-con-problema
git add -A
git commit -m "fix: corrección importante"
git push --force-with-lease  # Más seguro que --force

# NO uses scripts automáticos para force push
```

---

## Automatización con Hooks

### Escenario: Git hook para sincronizar automáticamente

Crear `.git/hooks/post-commit` en cada repo:

```bash
#!/bin/bash
# Post-commit hook para push automático

# Solo push si estamos en main
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ]; then
    echo "Auto-pushing to origin..."
    git push
fi
```

Hacer ejecutable:
```bash
chmod +x .git/hooks/post-commit
```

### Escenario: Script pre-commit para linting

```bash
#!/bin/bash
# Pre-commit hook para validar archivos

# Validar YAML
for file in $(git diff --cached --name-only | grep '\.yml$\|\.yaml$'); do
    python3 -c "import yaml; yaml.safe_load(open('$file'))" || exit 1
done

# Validar que index.qmd tenga formato correcto
for file in $(git diff --cached --name-only | grep 'index\.qmd$'); do
    if ! grep -q "title:" "$file"; then
        echo "Error: $file no tiene título"
        exit 1
    fi
done
```

---

## Scripts Personalizados

### Script para sincronizar solo blogs actualizados hoy

```bash
#!/bin/bash
# sync-today.sh

BASE_DIR="$HOME/Projects"

for repo in "$BASE_DIR"/*; do
    if [ -d "$repo/.git" ]; then
        cd "$repo"
        
        # Verificar si hay commits de hoy
        TODAY=$(date +%Y-%m-%d)
        if git log --since="$TODAY 00:00" --oneline | grep -q .; then
            echo "Sincronizando $(basename $repo)..."
            git push
        fi
    fi
done
```

### Script para backup antes de sincronizar

```bash
#!/bin/bash
# backup-and-sync.sh

BACKUP_DIR="$HOME/backups/repos-$(date +%Y%m%d)"
SOURCE_DIR="$HOME/Projects"

echo "Creando backup en $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

# Backup
for repo in "$SOURCE_DIR"/*; do
    if [ -d "$repo/.git" ]; then
        repo_name=$(basename "$repo")
        echo "  Respaldando $repo_name..."
        rsync -a --delete "$repo" "$BACKUP_DIR/"
    fi
done

echo "Backup completado. Sincronizando..."
./quick-sync.sh "$1"
```

### Script para generar changelog

```bash
#!/bin/bash
# generate-changelog.sh

OUTPUT="CHANGELOG.md"
echo "# Changelog - Actualización $(date +%Y-%m-%d)" > "$OUTPUT"
echo "" >> "$OUTPUT"

for repo in ~/Projects/*; do
    if [ -d "$repo/.git" ]; then
        cd "$repo"
        repo_name=$(basename "$repo")
        
        # Obtener commits desde hace 7 días
        commits=$(git log --since="7 days ago" --pretty=format:"- %s (%h)" 2>/dev/null)
        
        if [ -n "$commits" ]; then
            echo "## $repo_name" >> "$OUTPUT"
            echo "" >> "$OUTPUT"
            echo "$commits" >> "$OUTPUT"
            echo "" >> "$OUTPUT"
        fi
    fi
done

echo "Changelog generado en $OUTPUT"
```

---

## Casos de Uso Específicos

### Publicación de nuevo artículo

```bash
# 1. Crear artículo en uno o más blogs
cd ~/Projects/pecunia-fluxus/posts
mkdir 2025-12-19-analisis-inflacion
cd 2025-12-19-analisis-inflacion
# ... crear index.qmd ...

# 2. Regenerar índices
cd ~/Projects
python3 scripts/generar_indices.py

# 3. Sincronizar
cd ~/bin/git-sync
./sync-repos.py -m "feat: nuevo artículo sobre inflación 2025" -v
```

### Cambio masivo de configuración

```bash
# 1. Modificar _metadata.yml una sola vez (enlace duro)
cd ~/Projects/axiomata
nano _metadata.yml
# ... hacer cambios ...

# 2. Verificar cambios
cd ~/bin/git-sync
./sync-repos.sh -c

# 3. Sincronizar con mensaje descriptivo
./sync-repos.sh -m "feat(config): activar comentarios Giscus en todos los blogs"
```

### Actualización de dependencias

```bash
# 1. Actualizar Quarto en todos los proyectos
cd ~/Projects
for repo in */; do
    cd "$repo"
    quarto check
    # ... actualizar _quarto.yml si necesario ...
    cd ..
done

# 2. Sincronizar
cd ~/bin/git-sync
./sync-repos.sh -m "chore: actualizar a Quarto 1.4"
```

---

## Tips y Trucos

### Alias personalizados útiles

Agregar a `.bashrc` o `.zshrc`:

```bash
# Git sync aliases
alias gs='cd ~/bin/git-sync && ./quick-sync.sh'
alias gsc='cd ~/bin/git-sync && ./sync-repos.sh -c'
alias gsr='cd ~/bin/git-sync && ./repo-status.sh'

# Sync con timestamp
alias gst='cd ~/bin/git-sync && ./quick-sync.sh "update: $(date +%Y-%m-%d\ %H:%M)"'

# Sync específico
gsrepo() {
    cd ~/bin/git-sync && ./sync-repos.sh -r "$1" -m "$2"
}

# Ejemplo de uso:
# gs                                    # Sync rápido
# gst                                   # Sync con timestamp
# gsrepo "axiomata" "feat: nuevo post"  # Sync un repo específico
```

### Verificación antes de push importante

```bash
# Script: careful-sync.sh
#!/bin/bash

echo "Verificando cambios antes de sincronizar..."
./sync-repos.sh -c

read -p "¿Continuar con el push? (s/n): " confirm
if [[ $confirm == [sS] ]]; then
    ./sync-repos.sh -m "$1" -v
else
    echo "Cancelado"
fi
```

### Logs de sincronización

```bash
# Mantener un log de todas las sincronizaciones
echo "$(date): $1" >> ~/.git-sync-history
./quick-sync.sh "$1"

# Ver historial
tail -n 50 ~/.git-sync-history
```

---

## Solución de Problemas Comunes

### Problema: Repos fuera de sincronía

```bash
# Reset suave - actualizar todo desde remoto
cd ~/Projects
for repo in */; do
    cd "$repo"
    git fetch origin
    git reset --hard origin/main  # CUIDADO: perderás cambios locales
    cd ..
done
```

### Problema: Muchos archivos sin seguimiento

```bash
# Limpiar archivos ignorados
cd ~/Projects
for repo in */; do
    cd "$repo"
    git clean -fdx  # CUIDADO: elimina todo no rastreado
    cd ..
done
```

### Problema: Sincronización fallida en GitHub Actions

```bash
# Verificar permisos del token
cd ~/Projects/axiomata
git push -v  # Verbose para ver errores

# Actualizar token si necesario
git remote set-url origin https://TOKEN@github.com/user/repo.git
```

---

**Última actualización**: Diciembre 2025  
**Autor**: Edison Achalma
