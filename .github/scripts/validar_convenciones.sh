#!/usr/bin/env bash
# Reglas de ramas y commits de CLAUDE.md §4 y §6. Lo usa el job `convenciones` del CI.
#
#   validar_convenciones.sh rama <rama> <destino>
#   validar_convenciones.sh commit "<asunto del commit>"
set -euo pipefail

MODULOS='usuarios|inventario|clientes|campanias|reservas|costos|facturacion|auditoria|frontend|infra|docs'
KEBAB='[a-z0-9]+(-[a-z0-9]+)*'

validar_rama() {
  local rama="$1" destino="$2"
  if [[ "$rama" =~ ^(feature|fix)/($MODULOS)-$KEBAB$ ]] \
    || [[ "$rama" =~ ^(docs|chore)/$KEBAB$ ]]; then
    [[ "$destino" == "develop" ]] && return 0
    echo "La rama '$rama' solo puede apuntar a develop (apunta a $destino)."
    return 1
  fi
  if [[ "$rama" =~ ^hotfix/$KEBAB$ ]]; then
    [[ "$destino" == "main" ]] && return 0
    echo "La rama '$rama' solo puede apuntar a main (apunta a $destino)."
    return 1
  fi
  if [[ "$rama" == "develop" && "$destino" == "main" ]]; then
    return 0
  fi
  echo "La rama '$rama' no sigue el formato. Usá feature/<modulo>-<descripcion>,"
  echo "fix/<modulo>-<descripcion>, docs/<descripcion>, chore/<descripcion> o hotfix/<descripcion>."
  return 1
}

validar_commit() {
  local asunto="$1"
  [[ "$asunto" == "Merge "* ]] && return 0
  if [[ "$asunto" =~ ^(feat|fix|docs|refactor|test|chore|perf|ci)(\(($MODULOS)\))?:\ .{10,}$ ]]; then
    return 0
  fi
  echo "Commit inválido: '$asunto'. Formato: <tipo>(<modulo>): <descripción> (CLAUDE.md §6)."
  return 1
}

case "${1:-}" in
  rama) validar_rama "$2" "$3" ;;
  commit) validar_commit "$2" ;;
  *) echo "Uso: $0 rama <rama> <destino> | commit <asunto>"; exit 2 ;;
esac
