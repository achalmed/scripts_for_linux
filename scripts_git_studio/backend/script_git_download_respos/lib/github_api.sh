#!/usr/bin/env bash
# =============================================================================
# lib/github_api.sh — Consulta de repos vía API de GitHub
# =============================================================================
# Única responsabilidad: obtener la lista paginada de repos del usuario.
# Maneja explícitamente fallos de red y errores de la API (rate limit,
# usuario inexistente), que la v1.x dejaba pasar como errores crípticos.
#
# =============================================================================

# fetch_all_repos()
# Emite por stdout una línea "nombre|es_fork" por repo. Los logs van a
# stderr para no contaminar la lista. Si el usuario no tiene repos no
# emite nada (la v1.x emitía una línea vacía que luego se intentaba clonar).
fetch_all_repos() {
    local -a curl_auth=()
    [[ -n "${OPT_GH_TOKEN}" ]] && curl_auth=(-H "Authorization: Bearer ${OPT_GH_TOKEN}")

    local page=1 response repo_count
    while :; do
        if ! response=$(curl -sf --max-time 30 "${curl_auth[@]}" \
            "${GITHUB_API_URL}/users/${OPT_GH_USER}/repos?per_page=${GITHUB_API_PER_PAGE}&page=${page}&type=owner"); then
            # curl -f oculta el cuerpo en errores HTTP; repetimos sin -f
            # solo para extraer el mensaje real de la API
            response=$(curl -s --max-time 30 "${curl_auth[@]}" \
                "${GITHUB_API_URL}/users/${OPT_GH_USER}/repos?per_page=${GITHUB_API_PER_PAGE}&page=${page}&type=owner" || true)
            _report_api_error "${response}"
            exit 1
        fi

        repo_count=$(printf '%s' "${response}" | jq 'length')
        [[ "${repo_count}" -eq 0 ]] && break

        printf '%s' "${response}" | jq -r '.[] | "\(.name)|\(.fork)"'
        page=$((page + 1))
    done
}

# _report_api_error()
# Traduce la respuesta de error de la API (o su ausencia) a un mensaje útil.
#
# Arguments:
#   $1 - cuerpo de la respuesta HTTP (posiblemente vacío)
_report_api_error() {
    local response_body="$1"
    if [[ -z "${response_body}" ]]; then
        log_error "No se pudo contactar la API de GitHub (¿sin conexión?)."
        return
    fi
    local api_message
    api_message=$(printf '%s' "${response_body}" | jq -r '.message // "respuesta no reconocida"' 2>/dev/null \
        || printf 'respuesta no reconocida')
    log_error "Error de la API de GitHub: ${api_message}"
}
