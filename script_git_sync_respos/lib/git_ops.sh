#!/usr/bin/env bash
# =============================================================================
# lib/git_ops.sh
# -----------------------------------------------------------------------------
# Wrappers seguros alrededor de los comandos git usados por sync.sh y
# status.sh. Centraliza el manejo de errores y la detección de estado.
#
# BUGS CORREGIDOS RESPECTO AL ORIGINAL:
#   Bug 1 - git_has_local_changes: el original usaba 'git diff-index --quiet HEAD'
#            que falla con código 128 en repos sin ningún commit (recién clonados o
#            inicializados vacíos), invirtiendo la lógica de detección de cambios.
#            Ahora se verifica primero si HEAD existe antes de llamar diff-index.
#
#   Bug 2 - git_count_behind / git_count_ahead: el original comparaba directamente
#            contra la copia LOCAL de origin/ sin hacer fetch previo. Si no se
#            había hecho fetch en días, los contadores eran siempre 0 o incorrectos.
#            Ahora git_fetch_remote hace fetch --quiet antes de comparar, y las
#            funciones de conteo devuelven 0 si no hay upstream configurado
#            (en vez de fallar).
#
#   Bug 6 - git_has_remote_changes: el modo --check original solo veía cambios
#            locales sin commitear (diff-index), no detectaba commits remotos
#            pendientes de pull porque nunca hacía fetch. Ahora --check también
#            detecta "commits remotos disponibles".
# =============================================================================

[[ -n "${_GIT_OPS_LOADED:-}" ]] && return 0
readonly _GIT_OPS_LOADED=1

# =============================================================================
# git_is_repo PATH
#   Devuelve 0 si PATH existe y es un repositorio Git válido.
# =============================================================================
git_is_repo() {
    local path="$1"
    [[ -d "${path}/.git" ]]
}

# =============================================================================
# git_current_branch PATH
#   Imprime la rama actualmente activa en el repositorio.
# =============================================================================
git_current_branch() {
    git -C "$1" branch --show-current 2>/dev/null
}

# =============================================================================
# git_has_upstream PATH BRANCH
#   Devuelve 0 si la rama tiene un upstream remoto configurado.
# =============================================================================
git_has_upstream() {
    local path="$1" branch="$2"
    git -C "$path" rev-parse --abbrev-ref "${branch}@{upstream}" &>/dev/null
}

# =============================================================================
# git_fetch_remote PATH
#   Hace fetch --quiet al remoto origin.
#   Devuelve 0 si tuvo éxito, 1 si no hay remoto o falla la red.
#   El fallo es silencioso: si no hay conexión, los contadores quedarán en 0.
# =============================================================================
git_fetch_remote() {
    local path="$1"
    git -C "$path" fetch --quiet origin 2>/dev/null
}

# =============================================================================
# git_has_local_changes PATH
#   Devuelve 0 si hay archivos modificados/nuevos sin commitear.
#
#   CORRECCIÓN Bug 1: verifica la existencia de HEAD antes de llamar
#   diff-index para evitar exit-code 128 en repos sin commits.
# =============================================================================
git_has_local_changes() {
    local path="$1"

    # Repo recién creado sin ningún commit: cualquier archivo staged = cambio
    if ! git -C "$path" rev-parse HEAD &>/dev/null; then
        # Sin HEAD: hay cambios si hay algo en el staging area o en el workdir
        [[ -n "$(git -C "$path" status --porcelain 2>/dev/null)" ]]
        return $?
    fi

    # Repo normal: diff-index es confiable
    ! git -C "$path" diff-index --quiet HEAD -- 2>/dev/null
}

# =============================================================================
# git_count_uncommitted PATH
#   Imprime el número de archivos con cambios sin commitear.
# =============================================================================
git_count_uncommitted() {
    git -C "$1" status --short 2>/dev/null | wc -l | xargs
}

# =============================================================================
# git_count_ahead PATH BRANCH
#   Imprime cuántos commits locales NO están en origin/BRANCH.
#   Imprime 0 si no hay upstream o si la comparación falla.
# =============================================================================
git_count_ahead() {
    local path="$1" branch="$2"
    git_has_upstream "$path" "$branch" || { echo 0; return; }
    git -C "$path" rev-list "origin/${branch}..${branch}" --count 2>/dev/null || echo 0
}

# =============================================================================
# git_count_behind PATH BRANCH
#   Imprime cuántos commits de origin/BRANCH NO están en local.
#   Imprime 0 si no hay upstream o si la comparación falla.
# =============================================================================
git_count_behind() {
    local path="$1" branch="$2"
    git_has_upstream "$path" "$branch" || { echo 0; return; }
    git -C "$path" rev-list "${branch}..origin/${branch}" --count 2>/dev/null || echo 0
}

# =============================================================================
# git_last_commit_summary PATH
#   Imprime una línea resumen del último commit (hash + mensaje + tiempo).
# =============================================================================
git_last_commit_summary() {
    git -C "$1" log -1 --format="%h – %s (%cr)" 2>/dev/null || echo "(sin commits)"
}

# =============================================================================
# git_recent_commit_count PATH DAYS
#   Imprime el número de commits en los últimos DAYS días.
# =============================================================================
git_recent_commit_count() {
    local path="$1" days="${2:-7}"
    git -C "$path" log --since="${days} days ago" --oneline 2>/dev/null | wc -l | xargs
}

# =============================================================================
# git_pull PATH BRANCH VERBOSE
#   Hace git pull en PATH.
#   Si VERBOSE=true, muestra la salida completa.
#   Devuelve 0 si tuvo éxito, 1 si falló (ramas divergentes, conflictos, etc.)
# =============================================================================
git_pull() {
    local path="$1" branch="$2" verbose="${3:-false}"
    local err_file
    err_file="$(mktemp)"
    local result=0

    if [[ "$verbose" == "true" ]]; then
        git -C "$path" pull 2>"$err_file" || result=1
        [[ $result -ne 0 ]] && cat "$err_file" >&2
    else
        git -C "$path" pull --quiet 2>"$err_file" || result=1
        if [[ $result -ne 0 ]]; then
            # Mostrar solo las primeras líneas del error en modo no-verbose
            head -3 "$err_file" >&2
        fi
    fi

    rm -f "$err_file"
    return $result
}

# =============================================================================
# git_add_all PATH
#   Hace git add -A. Devuelve el exit code de git.
# =============================================================================
git_add_all() {
    git -C "$1" add -A 2>/dev/null
}

# =============================================================================
# git_commit PATH MESSAGE
#   Hace git commit -m MESSAGE. Devuelve el exit code de git.
# =============================================================================
git_commit() {
    local path="$1" message="$2"
    git -C "$path" commit --quiet -m "$message" 2>/dev/null
}

# =============================================================================
# git_push PATH VERBOSE
#   Hace git push. Devuelve el exit code de git.
# =============================================================================
git_push() {
    local path="$1" verbose="${2:-false}"
    if [[ "$verbose" == "true" ]]; then
        git -C "$path" push
    else
        git -C "$path" push --quiet 2>/dev/null
    fi
}
