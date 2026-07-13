#!/usr/bin/env bash
# =============================================================================
# lib/sync_engine.sh
# -----------------------------------------------------------------------------
# Motor de sincronización: procesa un repositorio individual haciendo
# pull → stage → commit → push con manejo de errores robusto.
#
# BUG CORREGIDO:
#   Bug 4 - El original llamaba process_repo dentro del loop principal con
#   'set -uo pipefail' activo. Cuando process_repo retornaba 2 (error),
#   la asignación result=$? era válida, PERO si el subshell generaba un
#   error no capturado antes del return, pipefail podía abortar el script
#   entero en vez de dejar que el loop continuara con el siguiente repo.
#   Ahora sync_process_repo captura todos los paths de error explícitamente
#   y nunca deja que un error no controlado burbujee hacia arriba.
#   Códigos de retorno:
#     0  → sincronizado con éxito
#     1  → sin cambios (no es error)
#     2  → error real (pull fallido, push fallido, etc.)
# =============================================================================

[[ -n "${_SYNC_ENGINE_LOADED:-}" ]] && return 0
readonly _SYNC_ENGINE_LOADED=1

# =============================================================================
# sync_process_repo NAME BRANCH OPTIONS...
#   Sincroniza un repositorio.
#
#   Opciones (variables del contexto del llamador):
#     COMMIT_MSG   Mensaje de commit
#     CHECK_ONLY   "true" → solo revisar, no commitear
#     VERBOSE      "true" → mostrar salida detallada de git
#     NO_PULL      "true" → no hacer git pull
#     BASE_DIR     Directorio base de repos
# =============================================================================
sync_process_repo() {
    local name="$1"
    local branch="$2"
    local repo_path="${BASE_DIR}/${name}"

    echo ""
    log_step "Procesando: ${name}"

    # Validaciones previas
    if [[ ! -d "$repo_path" ]]; then
        log_error "Directorio no encontrado: $repo_path"
        return 2
    fi

    if ! git_is_repo "$repo_path"; then
        log_error "No es un repositorio Git: $repo_path"
        return 2
    fi

    # Verificar rama activa
    local current_branch
    current_branch="$(git_current_branch "$repo_path")"
    if [[ "$current_branch" != "$branch" ]]; then
        log_warn "Rama activa: '${current_branch}', esperada: '${branch}'"
        log_warn "Continúo en la rama actual (no se hace checkout automático)"
        branch="$current_branch"
    fi

    # ─── git pull ────────────────────────────────────────────────────────────
    if [[ "${NO_PULL:-false}" == "false" ]] && [[ "${CHECK_ONLY:-false}" == "false" ]]; then
        log_info "Actualizando desde remoto (git pull)..."
        if ! git_pull "$repo_path" "$branch" "${VERBOSE:-false}"; then
            log_error "git pull falló en '${name}'"
            log_info  "Resuélvelo manualmente: cd ${repo_path} && git pull"
            log_info  "Puede haber ramas divergentes o conflictos de merge."
            return 2
        fi
        log_ok "Pull completado"
    fi

    # ─── Detectar cambios locales ─────────────────────────────────────────────
    if ! git_has_local_changes "$repo_path"; then
        # En modo --check, también verificar si hay commits remotos pendientes
        if [[ "${CHECK_ONLY:-false}" == "true" ]]; then
            git_fetch_remote "$repo_path" || true
            local behind
            behind="$(git_count_behind "$repo_path" "$branch")"
            if [[ "$behind" -gt 0 ]]; then
                log_warn "${name}: sin cambios locales, pero hay ${behind} commits remotos pendientes de pull"
                return 1
            fi
        fi
        log_warn "Sin cambios locales en '${name}'"
        return 1
    fi

    log_info "Cambios detectados en '${name}'"
    [[ "${VERBOSE:-false}" == "true" ]] && \
        git -C "$repo_path" status --short 2>/dev/null

    # ─── Modo verificación: mostrar y salir ───────────────────────────────────
    if [[ "${CHECK_ONLY:-false}" == "true" ]]; then
        log_info "Cambios pendientes:"
        git -C "$repo_path" status --short 2>/dev/null
        return 1
    fi

    # ─── git add -A ───────────────────────────────────────────────────────────
    log_info "Agregando cambios (git add -A)..."
    if ! git_add_all "$repo_path"; then
        log_error "Falló 'git add' en '${name}'"
        return 2
    fi

    # ─── git commit ───────────────────────────────────────────────────────────
    log_info "Creando commit: '${COMMIT_MSG}'"
    if ! git_commit "$repo_path" "$COMMIT_MSG"; then
        log_error "Falló 'git commit' en '${name}'"
        return 2
    fi

    # ─── git push ─────────────────────────────────────────────────────────────
    log_info "Enviando cambios (git push)..."
    if ! git_push "$repo_path" "${VERBOSE:-false}"; then
        log_error "Falló 'git push' en '${name}'"
        log_info  "Revisa conectividad y permisos del remoto."
        return 2
    fi

    log_ok "'${name}' sincronizado correctamente ✓"
    return 0
}
