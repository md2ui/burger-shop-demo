#!/usr/bin/env bash
# Writes the agent's md2ui notes (backend/md2ui_notes/) from the md2ui the backend runs and
# this app's theme, and lints the theme. Run it again whenever md2ui or the theme changes.
#
# The theme lives on the server side, in backend/md2ui_theme/: THEME.md and its fonts
# (what the window draws with, served at /theme) beside MEANINGS.md and patterns/ (what
# the agent is told). The notes hold md2ui's core note and the theme's part: its meanings
# (MEANINGS.md is the project's whole contract, THEME_GUIDE.md §10) and its patterns,
# written by md2ui itself.
#
# md2ui is the release backend/requirements.txt pins, installed in the backend's venv:
#   scripts/sync_md2ui.sh                       # the venv at backend/.venv
#   VENV=/path/to/venv scripts/sync_md2ui.sh
set -euo pipefail
cd "$(dirname "$0")/.."

VENV="${VENV:-backend/.venv}"
THEME="backend/md2ui_theme"
NOTES="backend/md2ui_notes"

mkdir -p "$NOTES"
# The core note ships inside the package (md2ui/shipped/skills/).
SHIPPED="$("$VENV/bin/python" -c 'from md2ui import session; print(session.resource_root())')"
cp "$SHIPPED/skills/README.md" "$NOTES/core.md"

# The lint runs first, so a pattern whose example fails `check` is named here rather
# than found missing in a reply.
"$VENV/bin/md2ui" check --theme "$THEME/THEME.md" 2>&1 | grep -v '^\[fonts\]' >&2
"$VENV/bin/python" - "$THEME/THEME.md" "$NOTES/theme.md" <<'PY'
import sys
from pathlib import Path

from md2ui import meanings

theme, out = Path(sys.argv[1]), Path(sys.argv[2])
patterns = meanings.theme_patterns(theme)
parts = [meanings.digest(theme, patterns).strip()]
parts += [f"## theme/{name}\n\n{path.read_text().strip()}" for name, path in patterns.items()]
out.write_text("# This theme\n\n" + "\n\n".join(parts) + "\n")
PY
echo "md2ui notes: $(wc -c < "$NOTES/core.md" | tr -d ' ') + $(wc -c < "$NOTES/theme.md" | tr -d ' ') bytes in $NOTES"
