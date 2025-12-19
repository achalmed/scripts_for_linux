# Scripts de Sincronización de Repositorios Git

Scripts para automatizar la sincronización de múltiples repositorios Git simultáneamente.

## 📁 Archivos

1. **`sync-repos.sh`** - Script bash completo con múltiples opciones
2. **`sync-repos.py`** - Script Python avanzado con auto-detección
3. **`quick-sync.sh`** - Script simplificado para uso rápido
4. **`repos-config.yml`** - Archivo de configuración

## 🚀 Instalación Rápida

### 1. Descargar los scripts

```bash
# Crear directorio para los scripts
mkdir -p ~/bin/git-sync
cd ~/bin/git-sync

# Los scripts ya están creados, solo necesitas moverlos
```

### 2. Dar permisos de ejecución

```bash
chmod +x sync-repos.sh
chmod +x sync-repos.py
chmod +x quick-sync.sh
```

### 3. Configurar tus repositorios

Edita el archivo correspondiente y modifica:

**Para `sync-repos.sh` y `quick-sync.sh`:**
```bash
# Cambiar esta línea con tu directorio real
BASE_DIR="$HOME/Projects"  # Por ejemplo: /home/edison/mis-blogs

# Y la lista de repos
REPOS=(
    "axiomata"
    "chaska"
    # ... tus repositorios
)
```

**Para `sync-repos.py`:**
Edita `repos-config.yml`:
```yaml
base_directory: ~/Projects  # Tu directorio real
```

## 💻 Uso

### Opción 1: Script Simplificado (Recomendado para uso diario)

```bash
# Sincronizar todos con mensaje por defecto
./quick-sync.sh

# Con mensaje personalizado
./quick-sync.sh "feat: actualizar configuración"
```

### Opción 2: Script Bash Completo

```bash
# Sincronizar todos los repos
./sync-repos.sh

# Con mensaje personalizado
./sync-repos.sh -m "feat: actualizar índices"

# Solo verificar cambios (sin commit/push)
./sync-repos.sh -c

# Sincronizar solo repos específicos
./sync-repos.sh -r "axiomata,chaska"

# Modo verbose
./sync-repos.sh -v

# Ver todas las opciones
./sync-repos.sh -h
```

### Opción 3: Script Python (Más avanzado)

```bash
# Instalar dependencia primero
pip install pyyaml --break-system-packages

# Sincronizar todos
./sync-repos.py

# Con auto-detección de tipo de commit
./sync-repos.py -v

# Solo repos específicos
./sync-repos.py -r axiomata chaska

# Solo verificar
./sync-repos.py -c

# Modo paralelo (más rápido)
./sync-repos.py --parallel

# Ver ayuda completa
./sync-repos.py -h
```

## 🎯 Ejemplos Prácticos

### Escenario 1: Actualización diaria rápida

```bash
# Cada día al finalizar tu trabajo
./quick-sync.sh "update: cambios del $(date +%Y-%m-%d)"
```

### Escenario 2: Actualización de _metadata.yml (archivo de enlace duro)

```bash
# Como _metadata.yml se actualiza en todos los repos
./sync-repos.sh -m "feat(config): actualizar metadata global"
```

### Escenario 3: Actualización de índices por scripts

```bash
# Los scripts actualizaron todos los índices
./sync-repos.py -m "docs: actualizar índices automáticos" -v
```

### Escenario 4: Verificar qué cambió antes de sincronizar

```bash
# Ver cambios sin hacer commit
./sync-repos.sh -c

# Si todo está bien, sincronizar
./sync-repos.sh -m "docs: actualizar contenidos"
```

### Escenario 5: Solo actualizar algunos blogs específicos

```bash
# Solo blogs de economía
./sync-repos.sh -r "pecunia-fluxus,epsilon-y-beta,optimums" \
    -m "feat: añadir análisis económico Q4"
```

## 🔧 Configuración Avanzada

### Alias en tu shell

Agrega a tu `~/.bashrc` o `~/.zshrc`:

```bash
# Alias para sincronización rápida
alias gsync='~/bin/git-sync/quick-sync.sh'
alias gsync-check='~/bin/git-sync/sync-repos.sh -c'
alias gsync-all='~/bin/git-sync/sync-repos.py --parallel -v'

# Función para sincronizar con mensaje
gsyncm() {
    ~/bin/git-sync/quick-sync.sh "$1"
}
```

Luego recarga:
```bash
source ~/.bashrc  # o source ~/.zshrc
```

Ahora puedes usar:
```bash
gsync                                    # Sincronización rápida
gsyncm "feat: nueva característica"      # Con mensaje
gsync-check                              # Solo verificar
```

### Automatización con Cron

Para sincronizar automáticamente cada día:

```bash
# Editar crontab
crontab -e

# Agregar línea (sincronizar a las 6 PM cada día)
0 18 * * * /home/edison/bin/git-sync/quick-sync.sh "auto: sincronización diaria" >> /tmp/git-sync.log 2>&1
```

### Integración con VS Code / Positron

Crear tarea en `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Sync All Repos",
            "type": "shell",
            "command": "${workspaceFolder}/../git-sync/quick-sync.sh",
            "args": ["update: sincronización desde VS Code"],
            "problemMatcher": []
        },
        {
            "label": "Check Repo Changes",
            "type": "shell",
            "command": "${workspaceFolder}/../git-sync/sync-repos.sh",
            "args": ["-c"],
            "problemMatcher": []
        }
    ]
}
```

## 🎨 Personalización del archivo de configuración

### Mensajes de commit inteligentes

El script Python puede auto-detectar el tipo de cambio:

```yaml
# En repos-config.yml
commit_messages:
  metadata: "feat(config): actualizar configuración del sitio"
  theme: "style: actualizar tema y estilos"
  content: "docs: actualizar contenidos"
  indices: "docs: regenerar índices"
  scripts: "chore: actualizar scripts"

auto_detect_patterns:
  metadata:
    - "_metadata.yml"
    - "_quarto.yml"
  theme:
    - "styles.css"
    - "*.scss"
  indices:
    - "**/index.qmd"
```

### Configuración por repositorio

```yaml
repositories:
  - name: axiomata
    branch: main
    enabled: true
    
  - name: chaska
    branch: main
    enabled: true
    
  - name: experimental-blog
    branch: develop  # Rama diferente
    enabled: false   # Deshabilitado temporalmente
```

## 🐛 Solución de Problemas

### Error: "Permission denied"
```bash
chmod +x sync-repos.sh quick-sync.sh sync-repos.py
```

### Error: "No such file or directory"
Verifica la ruta en `BASE_DIR`:
```bash
# Ver dónde están tus repos
ls -la ~/Projects
# o
ls -la ~/repos
# o donde sea que estén
```

### Error: "ModuleNotFoundError: No module named 'yaml'"
```bash
pip install pyyaml --break-system-packages
```

### Los cambios no se detectan
```bash
# Verificar estado de un repo manualmente
cd ~/Projects/axiomata
git status
```

### Conflictos de merge
El script hace `pull` antes de `push`. Si hay conflictos:
```bash
# Resolver manualmente
cd ~/Projects/nombre-repo
git status
# Resolver conflictos
git add .
git commit
git push
```

## 📊 Comparación de Scripts

| Característica | quick-sync.sh | sync-repos.sh | sync-repos.py |
|----------------|---------------|---------------|---------------|
| Velocidad | ⚡⚡⚡ | ⚡⚡ | ⚡ |
| Simplicidad | ✅✅✅ | ✅✅ | ✅ |
| Auto-detección | ❌ | ❌ | ✅ |
| Configuración | Código | Código | YAML |
| Procesamiento paralelo | ❌ | ❌ | ✅ |
| Modo verbose | ❌ | ✅ | ✅ |
| Reintentos automáticos | ❌ | ❌ | ✅ |
| Dependencias | Ninguna | Ninguna | Python + PyYAML |

## 🎓 Recomendaciones

1. **Para uso diario**: Usa `quick-sync.sh`
2. **Para control detallado**: Usa `sync-repos.sh`
3. **Para automatización avanzada**: Usa `sync-repos.py`

## 📝 Notas Importantes

- ⚠️ Los scripts hacen `git push --force` NO, solo `git push` normal
- 📦 Recomendado: Hacer `git pull` antes si trabajas en múltiples máquinas
- 🔒 Los archivos de enlace duro (_metadata.yml) se sincronizan automáticamente
- 💾 Siempre puedes deshacer con `git reset` si algo sale mal

## 🤝 Flujo de Trabajo Recomendado

```bash
# 1. Al iniciar el día (opcional)
cd ~/Projects
for repo in */; do cd "$repo" && git pull && cd ..; done

# 2. Trabajar normalmente en tus blogs...

# 3. Al finalizar, verificar cambios
./git-sync/sync-repos.sh -c

# 4. Si todo está bien, sincronizar
./git-sync/quick-sync.sh "update: contenidos del día"

# 5. (Opcional) Verificar en GitHub que todo subió correctamente
```

## 📚 Recursos Adicionales

- [Documentación Git](https://git-scm.com/doc)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub - Manejo de múltiples repos](https://docs.github.com/en/get-started)

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs: `./sync-repos.sh -v`
2. Verifica configuración: `cat repos-config.yml`
3. Prueba con un solo repo primero: `./sync-repos.sh -r "axiomata"`

---

**Autor**: Edison Achalma  
**Última actualización**: Diciembre 2025  
**Licencia**: MIT
