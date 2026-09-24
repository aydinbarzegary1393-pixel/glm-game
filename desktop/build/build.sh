#!/usr/bin/env bash
# GLM FPS Game - Windows Setup builder (Linux, no root needed)
# Stages game + Electron runtime, then compiles NSIS installer.
set -euo pipefail

DESK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # desktop/
ROOT="$(dirname "$DESK")"                                  # repo root
TOOLS="/home/z/my-project/tools"
ELEC_VER="22.3.27"
CACHE="$TOOLS/cache"
MAKENSIS="$TOOLS/nsis-root/usr/bin/makensis"
export NSISDIR="$TOOLS/nsis-root/usr/share/nsis"   # portable makensis data dir

STAGE="$DESK/staging"
APPROOT="$STAGE/app-root"

echo "[1/6] clean staging + dist"
rm -rf "$STAGE" "$DESK/dist"
mkdir -p "$APPROOT/resources/app/game" "$DESK/dist"

echo "[2/6] copy game files (html + assets)"
cp "$ROOT/fps-game.html" "$APPROOT/resources/app/game/"
cp -r "$ROOT/fps-game-assets" "$APPROOT/resources/app/game/"

echo "[3/6] copy app sources (main.js, package.json, icons)"
cp "$DESK/app/package.json" "$DESK/app/main.js" "$APPROOT/resources/app/"
cp "$DESK/app/app-icon.png" "$DESK/app/app-icon.ico" "$APPROOT/resources/app/"

echo "[4/6] electron runtime v$ELEC_VER (win32-x64)"
if [ ! -f "$CACHE/electron-v$ELEC_VER-win32-x64.zip" ]; then
  mkdir -p "$CACHE"
  curl -L -C - --fail --retry 3 -o "$CACHE/electron-v$ELEC_VER-win32-x64.zip" \
    "https://github.com/electron/electron/releases/download/v$ELEC_VER/electron-v$ELEC_VER-win32-x64.zip"
fi
unzip -q -o "$CACHE/electron-v$ELEC_VER-win32-x64.zip" -d "$APPROOT"
mv "$APPROOT/electron.exe" "$APPROOT/GLMFPSGame.exe"
rm -f "$APPROOT/LICENSE.electron.txt" "$APPROOT/LICENSES.chromium.html" "$APPROOT/resources/default_app.asar"

echo "[5/6] estimated size -> size.nsh"
KB=$(du -sk "$APPROOT" | cut -f1)
printf '!define ESTSIZE_KB %s\n' "$KB" > "$DESK/build/size.nsh"
echo "      ESTSIZE_KB=$KB"

echo "[6/6] makensis (LZMA solid, may take minutes)"
cd "$DESK/build"
"$MAKENSIS" -V2 installer.nsi

echo "DONE: $DESK/dist/GLM-FPS-Game-Setup-${APPVER}.exe"
