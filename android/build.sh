#!/usr/bin/env bash
# Build the GLM FPS Android APK (no Gradle needed).
# Requirements (already provisioned under /home/z/my-project/tools/android):
#   - build-tools 33.0.2 (aapt2, d8, apksigner, zipalign) + platform-33 android.jar
#   - ecj.jar (Eclipse compiler for Java, runs on the system JRE)
# Output: /home/z/my-project/download/GLM-FPS-Game-Android-<ver>.apk
set -euo pipefail

TOOLS_DIR="/home/z/my-project/tools/android"
BT="$TOOLS_DIR/android-13"
ECJ="$TOOLS_DIR/ecj.jar"
REPO="/home/z/my-project/glm-game"
PROJ="$REPO/android"
BUILD="$TOOLS_DIR/apk-build"
OUT="/home/z/my-project/download"

VERSION_CODE=1
VERSION_NAME="1.0.0"
PKG="com.glmgame.fps"
APK_NAME="GLM-FPS-Game-Android-$VERSION_NAME.apk"

ANDROID_JAR="$BT/android.jar"

echo "== [1/6] bundle game files =="
rm -rf "$BUILD"
mkdir -p "$BUILD/classes" "$BUILD/dex" "$OUT"
mkdir -p "$BUILD/assets/game"
cp "$REPO/fps-game.html"            "$BUILD/assets/game/"
cp -r "$REPO/fps-game-assets"       "$BUILD/assets/game/"
cp "$REPO/version.json"             "$BUILD/assets/game/version.json"

echo "== [2/6] aapt2 compile + link =="
"$BT/aapt2" compile --dir "$PROJ/res" -o "$BUILD/res.zip"
"$BT/aapt2" link -o "$BUILD/base.apk" \
  -I "$ANDROID_JAR" \
  --manifest "$PROJ/AndroidManifest.xml" \
  --min-sdk-version 21 --target-sdk-version 33 \
  --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" \
  --auto-add-overlay \
  -A "$BUILD/assets" \
  "$BUILD/res.zip"

echo "== [3/6] compile java (ecj) =="
mapfile -t SRCS < <(find "$PROJ/src" -name '*.java')
java -jar "$ECJ" -nowarn -source 8 -target 8 -encoding UTF-8 \
  -classpath "$ANDROID_JAR" \
  -d "$BUILD/classes" \
  "${SRCS[@]}"

echo "== [4/6] dex (d8) =="
mapfile -t CLASSES < <(find "$BUILD/classes" -name '*.class')
"$BT/d8" --release --lib "$ANDROID_JAR" --min-api 21 \
  --output "$BUILD/dex" \
  "${CLASSES[@]}"
test -f "$BUILD/dex/classes.dex"

echo "== [5/6] pack =="
cp "$BUILD/base.apk" "$BUILD/unsigned.apk"
(cd "$BUILD/dex" && zip -q -j ../unsigned.apk classes.dex)
"$BT/zipalign" -f 4 "$BUILD/unsigned.apk" "$BUILD/aligned.apk"

echo "== [6/6] sign =="
KS="$PROJ/keystore/glm-release.jks"
if [ ! -f "$KS" ]; then
  echo "  generating release keystore..."
  keytool -genkeypair -keystore "$KS" -alias glmfps \
    -keyalg RSA -keysize 2048 -validity 10950 \
    -storepass glmgame123 -keypass glmgame123 \
    -dname "CN=GLM FPS, O=aydinbarzegary1393, C=IR"
fi
"$BT/apksigner" sign \
  --ks "$KS" --ks-pass pass:glmgame123 --key-pass pass:glmgame123 \
  --out "$OUT/$APK_NAME" "$BUILD/aligned.apk"
"$BT/apksigner" verify "$OUT/$APK_NAME"

SIZE=$(du -h "$OUT/$APK_NAME" | cut -f1)
SHA=$(sha256sum "$OUT/$APK_NAME" | cut -d' ' -f1)
echo "APK OK: $OUT/$APK_NAME ($SIZE)"
echo "SHA-256: $SHA"
