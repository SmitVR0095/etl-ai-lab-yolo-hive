#!/usr/bin/env bash
set -Eeuo pipefail

# Wrapper para ejecutar un comando y enviar notificación Telegram al iniciar/finalizar/fallar.
# Uso:
#   bash scripts/run_with_telegram.sh "Nombre del proceso" comando arg1 arg2 ...

if [ "$#" -lt 2 ]; then
  echo "Uso: $0 \"Nombre del proceso\" comando arg1 arg2 ..." >&2
  exit 2
fi

TASK_NAME="$1"
shift

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOTIFIER="$PROJECT_ROOT/scripts/telegram_notify.py"

python "$NOTIFIER" --optional --message "🚀 INICIO: ${TASK_NAME}"

set +e
"$@"
STATUS=$?
set -e

if [ "$STATUS" -eq 0 ]; then
  python "$NOTIFIER" --optional --message "✅ FIN OK: ${TASK_NAME}"
else
  python "$NOTIFIER" --optional --message "❌ ERROR: ${TASK_NAME} | Código: ${STATUS}"
fi

exit "$STATUS"
