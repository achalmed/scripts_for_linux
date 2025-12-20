#!/bin/bash

# Script para sincronizar múltiples repositorios Git
# Autor: Edison Achalma
# Descripción: Automatiza git add, commit y push para múltiples repositorios

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Directorio base donde están tus repositorios
# Modifica esta ruta según tu configuración
BASE_DIR="$HOME/Documents/publicaciones"

# Lista de repositorios (nombres de carpetas)
REPOS=(
    "actus-mercator"
    "aequilibria"
    "axiomata"
    "chaska"
    "dialectica-y-mercado"
    "epsilon-y-beta"
    "methodica"
    "numerus-scriptum"
    "optimums"
    "pecunia-fluxus"
    "res-publica"
    "website-achalma"
)

# Mensaje de commit por defecto
DEFAULT_COMMIT_MSG="update: sincronización automática de contenidos"

# Función para mostrar ayuda
show_help() {
    cat << EOF
Uso: $0 [OPCIONES]

Opciones:
    -m, --message "mensaje"    Mensaje personalizado para el commit
    -r, --repos "repo1,repo2"  Sincronizar solo repositorios específicos (separados por coma)
    -d, --dir "directorio"     Directorio base donde están los repositorios
    -c, --check                Solo verificar cambios sin hacer commit/push
    -h, --help                 Mostrar esta ayuda
    -v, --verbose              Modo verbose (más detalles)

Ejemplos:
    $0                                           # Sincronizar todos los repos con mensaje por defecto
    $0 -m "feat: actualizar configuración"       # Mensaje personalizado
    $0 -r "axiomata,chaska"                      # Solo repos específicos
    $0 -c                                        # Solo verificar cambios
    $0 -m "docs: actualizar índices" -v          # Con modo verbose

EOF
}

# Función para procesar un repositorio
process_repo() {
    local repo_path="$1"
    local repo_name="$2"
    local commit_msg="$3"
    local check_only="$4"
    local verbose="$5"
    
    echo ""
    echo "=========================================="
    print_info "Procesando: ${YELLOW}$repo_name${NC}"
    echo "=========================================="
    
    # Verificar si existe el directorio
    if [ ! -d "$repo_path" ]; then
        print_error "Directorio no encontrado: $repo_path"
        return 1
    fi
    
    cd "$repo_path" || return 1
    
    # Verificar si es un repositorio git
    if [ ! -d ".git" ]; then
        print_error "No es un repositorio Git: $repo_path"
        return 1
    fi
    
    # Verificar el estado del repositorio
    if [ "$verbose" = true ]; then
        print_info "Verificando estado del repositorio..."
        git status
    fi
    
    # Verificar si hay cambios
    if git diff-index --quiet HEAD --; then
        print_warning "No hay cambios en $repo_name"
        return 0
    fi
    
    print_info "Cambios detectados en $repo_name"
    
    # Si es solo verificación, mostrar cambios y salir
    if [ "$check_only" = true ]; then
        git status --short
        return 0
    fi
    
    # Hacer git add
    print_info "Agregando cambios al staging area..."
    git add -A
    
    if [ $? -ne 0 ]; then
        print_error "Error al ejecutar git add en $repo_name"
        return 1
    fi
    
    # Hacer git commit
    print_info "Creando commit..."
    git commit -m "$commit_msg"
    
    if [ $? -ne 0 ]; then
        print_error "Error al ejecutar git commit en $repo_name"
        return 1
    fi
    
    # Hacer git push
    print_info "Enviando cambios al repositorio remoto..."
    git push
    
    if [ $? -eq 0 ]; then
        print_success "✓ $repo_name sincronizado exitosamente"
    else
        print_error "Error al ejecutar git push en $repo_name"
        return 1
    fi
    
    return 0
}

# Parsear argumentos
COMMIT_MSG="$DEFAULT_COMMIT_MSG"
SELECTED_REPOS=()
CHECK_ONLY=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--message)
            COMMIT_MSG="$2"
            shift 2
            ;;
        -r|--repos)
            IFS=',' read -ra SELECTED_REPOS <<< "$2"
            shift 2
            ;;
        -d|--dir)
            BASE_DIR="$2"
            shift 2
            ;;
        -c|--check)
            CHECK_ONLY=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Si no se especificaron repos, usar todos
if [ ${#SELECTED_REPOS[@]} -eq 0 ]; then
    SELECTED_REPOS=("${REPOS[@]}")
fi

# Inicio del proceso
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       SCRIPT DE SINCRONIZACIÓN DE REPOSITORIOS GIT        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
print_info "Directorio base: $BASE_DIR"
print_info "Mensaje de commit: $COMMIT_MSG"
print_info "Repositorios a procesar: ${#SELECTED_REPOS[@]}"

if [ "$CHECK_ONLY" = true ]; then
    print_warning "Modo verificación activado (no se harán commits ni push)"
fi

echo ""

# Contadores
SUCCESS_COUNT=0
ERROR_COUNT=0
NO_CHANGES_COUNT=0

# Procesar cada repositorio
for repo in "${SELECTED_REPOS[@]}"; do
    repo_path="$BASE_DIR/$repo"
    
    if process_repo "$repo_path" "$repo" "$COMMIT_MSG" "$CHECK_ONLY" "$VERBOSE"; then
        if git -C "$repo_path" diff-index --quiet HEAD --; then
            ((NO_CHANGES_COUNT++))
        else
            ((SUCCESS_COUNT++))
        fi
    else
        ((ERROR_COUNT++))
    fi
done

# Resumen final
echo ""
echo "=========================================="
echo "          RESUMEN DE SINCRONIZACIÓN       "
echo "=========================================="
print_success "Exitosos: $SUCCESS_COUNT"
print_warning "Sin cambios: $NO_CHANGES_COUNT"
print_error "Errores: $ERROR_COUNT"
echo "=========================================="
echo ""

# Salir con código de error si hubo algún fallo
if [ $ERROR_COUNT -gt 0 ]; then
    exit 1
else
    exit 0
fi
