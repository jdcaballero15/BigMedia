#!/usr/bin/env bash
# Prueba validar_convenciones.sh. Lo corre el job `convenciones` antes de usarlo.
set -uo pipefail
script="$(dirname "$0")/validar_convenciones.sh"
fallos=0

acepta() { bash "$script" "$@" >/dev/null || { echo "Debía aceptar: $*"; fallos=1; }; }
rechaza() { ! bash "$script" "$@" >/dev/null || { echo "Debía rechazar: $*"; fallos=1; }; }

acepta rama feature/inventario-capacidad-por-cartel develop
acepta rama fix/reservas-dia-de-borde develop
acepta rama docs/historias-cancelacion develop
acepta rama chore/gates-de-calidad develop
acepta rama hotfix/login-caido main
acepta rama develop main
rechaza rama feature/capacidad develop
rechaza rama feature/ventas-algo develop
rechaza rama feature/inventario-capacidad main
rechaza rama hotfix/login-caido develop
rechaza rama docs/Historias develop
rechaza rama feat/inventario develop
rechaza rama main develop

acepta commit "feat(inventario): add poster capacity override"
acepta commit "docs: migrate requirements to aidlc inputs"
acepta commit "Merge pull request #12 from jdcaballero15/feature/x"
rechaza commit "WIP"
rechaza commit "feat(ventas): add something long enough"
rechaza commit "feat: corto"
rechaza commit "Feat(inventario): add poster capacity override"

[ "$fallos" -eq 0 ] && echo "validar_convenciones.sh: todos los casos pasan."
exit "$fallos"
