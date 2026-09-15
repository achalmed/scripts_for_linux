#!/usr/bin/env bash
# =============================================================================
# lib/validator.sh — Validación de dependencias y opciones
# =============================================================================
# La v1.x pasaba valores sin validar directamente a git y curl, lo que
# producía errores crípticos; aquí toda opción se comprueba antes de
# tocar la red o el disco.
#
# =============================================================================

# validate_dependencies()
# git siempre; curl y jq solo hacen falta en modo "all" (consulta a la API).
validate_dependencies() {
    local -a required=(git)
    [[ "${OPT_MODE}" == "all" ]] && required+=(curl jq)

    local cmd
    for cmd in "${required[@]}"; do
        if ! command -v "${cmd}" > /dev/null 2>&1; then
            log_error "Falta el comando '${cmd}'. Instálalo antes de continuar."
            log_error "  Kubuntu/Debian: sudo apt install ${cmd}   |   Arch: sudo pacman -S ${cmd}"
            exit 5
        fi
    done
}

# validate_options()
# Comprueba coherencia de usuario, modo, protocolo y profundidad.
validate_options() {
    if [[ -z "${OPT_GH_USER}" ]]; then
        log_error "Falta especificar el usuario con -u."
        show_help >&2
        exit 2
    fi

    case "${OPT_MODE}" in
        all) ;;
        list|single)
            if [[ -z "${OPT_REPO_LIST}" ]]; then
                log_error "El modo '${OPT_MODE}' requiere -r con el/los repos."
                exit 2
            fi
            ;;
        *)
            log_error "Modo inválido: '${OPT_MODE}'. Usa all, list o single."
            exit 2
            ;;
    esac

    if [[ "${OPT_PROTOCOL}" != "ssh" ]] && [[ "${OPT_PROTOCOL}" != "https" ]]; then
        # La v1.x aceptaba cualquier valor y caía a https en silencio
        log_error "Protocolo inválido: '${OPT_PROTOCOL}'. Usa ssh o https."
        exit 2
    fi

    if [[ "${OPT_DEPTH}" != "full" ]] && ! [[ "${OPT_DEPTH}" =~ ^[0-9]+$ ]]; then
        log_error "Profundidad inválida: '${OPT_DEPTH}'. Usa un número, 0 o 'full'."
        exit 2
    fi
}

# prepare_dest_dir()
# Crea la carpeta destino y entra en ella; los clones usan rutas
# relativas a partir de aquí.
prepare_dest_dir() {
    if ! mkdir -p "${OPT_DEST_DIR}"; then
        log_error "No se pudo crear la carpeta destino '${OPT_DEST_DIR}'."
        exit 4
    fi
    cd "${OPT_DEST_DIR}"
    log_verbose "Carpeta destino: $(pwd)"
}
