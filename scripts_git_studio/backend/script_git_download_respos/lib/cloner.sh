#!/usr/bin/env bash
# =============================================================================
# lib/cloner.sh — Clonado de repositorios
# =============================================================================
# Construcción de URL y flags de git clone, clonado individual y
# contadores de resultado para el resumen final.
#
# =============================================================================

declare -g COUNT_CLONED=0
declare -g COUNT_SKIPPED=0
declare -g COUNT_FAILED=0

# build_clone_flags()
# Llena por nameref el array de flags de git clone. Se usa un array real
# (no un string spliteado con read) para que ramas con espacios o
# caracteres glob no se rompan — ese era un bug de la v1.x.
#
# Arguments:
#   $1 - nombre del array destino (nameref)
build_clone_flags() {
    local -n flags_ref="$1"
    flags_ref=()
    if [[ "${OPT_DEPTH}" != "full" ]] && [[ "${OPT_DEPTH}" != "0" ]]; then
        flags_ref+=(--depth "${OPT_DEPTH}")
    fi
    if [[ -n "${OPT_BRANCH}" ]]; then
        flags_ref+=(--branch "${OPT_BRANCH}" --single-branch)
    fi
}

# build_clone_url()
# Arguments:
#   $1 - nombre del repo
build_clone_url() {
    local repo_name="$1"
    if [[ "${OPT_PROTOCOL}" == "ssh" ]]; then
        printf 'git@github.com:%s/%s.git' "${OPT_GH_USER}" "${repo_name}"
    else
        printf 'https://github.com/%s/%s.git' "${OPT_GH_USER}" "${repo_name}"
    fi
}

# clone_repo()
# Clona un repo en una subcarpeta homónima; omite si ya existe y
# respeta dry-run. Actualiza los contadores globales.
#
# Arguments:
#   $1 - nombre del repo
clone_repo() {
    local repo_name="$1"
    local clone_url
    clone_url="$(build_clone_url "${repo_name}")"

    if [[ -d "${repo_name}" ]]; then
        log_warn "La carpeta '${repo_name}' ya existe, se omite. (Bórrala o muévela para re-descargarla)"
        COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
        return
    fi

    if [[ "${OPT_DRY_RUN}" == "true" ]]; then
        printf "${CLR_INFO}[DRY-RUN]${CLR_RESET} Se clonaría: %s (profundidad: %s)\n" \
            "${clone_url}" "${OPT_DEPTH}"
        COUNT_CLONED=$((COUNT_CLONED + 1))
        return
    fi

    local -a clone_flags
    build_clone_flags clone_flags

    log_info "Clonando ${repo_name} (profundidad: ${OPT_DEPTH})..."
    if git clone "${clone_flags[@]}" "${clone_url}" "${repo_name}" 2>&1 | sed 's/^/    /'; then
        _finish_clone "${repo_name}"
    else
        log_error "Falló la descarga de ${repo_name}."
        COUNT_FAILED=$((COUNT_FAILED + 1))
    fi
}

# _finish_clone()
# Post-procesado de un clon exitoso: strip opcional de .git y contador.
#
# Arguments:
#   $1 - nombre del repo recién clonado
_finish_clone() {
    local repo_name="$1"
    if [[ "${OPT_STRIP_GIT}" == "true" ]]; then
        rm -rf "${repo_name}/.git"
        log_ok "${repo_name} descargado (snapshot sin historial git)."
    else
        log_ok "${repo_name} descargado."
    fi
    COUNT_CLONED=$((COUNT_CLONED + 1))
}

# is_excluded_repo()
# Comprueba si un repo está en la lista de exclusión (-x), tolerando
# espacios alrededor de las comas.
#
# Arguments:
#   $1 - nombre del repo
#
# Returns:
#   0 si está excluido, 1 si no
is_excluded_repo() {
    local repo_name="$1"
    [[ -z "${OPT_EXCLUDE_LIST}" ]] && return 1

    local -a excludes
    IFS=',' read -ra excludes <<< "${OPT_EXCLUDE_LIST}"
    local excluded
    for excluded in "${excludes[@]}"; do
        excluded="${excluded#"${excluded%%[![:space:]]*}"}"
        excluded="${excluded%"${excluded##*[![:space:]]}"}"
        [[ "${repo_name}" == "${excluded}" ]] && return 0
    done
    return 1
}
