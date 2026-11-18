#!/usr/bin/env bash
# Builds the md2ui page the app's web view shows (web/embed.html, with the @md2ui/dom and
# @md2ui/wire releases web/package.json pins) into assets/md2ui, copies the shop's theme
# beside it (THEME.md, its fonts and md2ui's icon font, from backend/md2ui_theme: the same
# theme the backend's agent writes for), and lists every asset folder in pubspec.yaml
# (Flutter asset folders are not recursive).
#
# Run it again whenever those pins, web/src/embed.ts or the theme change:
#   tool/sync_md2ui.sh
#
# The faces copied here are the ones lib/md2ui/theme.dart lists: keep the two in step.
set -euo pipefail
cd "$(dirname "$0")/.."

DEST="assets/md2ui"
THEME="../backend/md2ui_theme"

(cd ../web && pnpm install --silent && EMBED_OUT="$PWD/../app/$DEST" pnpm exec vite build -c vite.embed.config.ts --logLevel warn)

# The theme keeps md2ui's layout: its asset paths resolve beside THEME.md.
mkdir -p "$DEST/theme/assets/fonts" "$DEST/theme/assets/icons"
cp "$THEME/THEME.md" "$DEST/theme/THEME.md"
cp "$THEME"/assets/fonts/*.ttf "$THEME"/assets/fonts/*-OFL.txt "$DEST/theme/assets/fonts/"
cp "$THEME/assets/icons/material-design-icons-md2ui.ttf" "$DEST/theme/assets/icons/"

# Rewrite the generated block between the markers in pubspec.yaml.
dirs="$(mktemp)"
(cd "$DEST" && find . -type d | sort) | sed "s|^\.||; s|^|    - $DEST|; s|\$|/|" > "$dirs"
awk -v dirs="$dirs" '
  /# md2ui-assets:start/ { print; while ((getline line < dirs) > 0) print line; skip = 1; next }
  /# md2ui-assets:end/   { skip = 0 }
  !skip
' pubspec.yaml > pubspec.yaml.tmp && mv pubspec.yaml.tmp pubspec.yaml
rm -f "$dirs"

echo "md2ui page: $(find "$DEST" -type f | wc -l | tr -d ' ') files, $(du -sh "$DEST" | cut -f1) in $DEST"
