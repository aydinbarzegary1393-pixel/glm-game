# GLM FPS — Android Edition

بازی به‌صورت APK اندرویدی با **آپدیت خودکار از گیت‌هاب**. (Android APK with GitHub auto-update.)

## نصب / Install
1. `GLM-FPS-Game-Android-1.0.0.apk` را دانلود کنید (از صفحه Releases).
2. فایل را روی گوشی باز کنید؛ اگر پیام «منابع ناشناس» آمد، اجازه نصب را بدهید.
3. بازی را باز کنید — نیازی به اینترنت برای بازی کردن نیست.

## آپدیت خودکار / Auto-update
روی شروعِ هر اجرا (اسپلش):
- اگر اینترنت باشد: `version.json` از GitHub Pages خوانده می‌شود؛ اگر نسخه‌ی جدیدتری منتشر شده باشد، **فقط فایل‌های تغییرکرده** دانلود و SHA-256 هر فایل تأیید می‌شود، بعد بازی اجرا می‌شود.
- اگر اینترنت نباشد یا چک شکست بخورد: بلافاصله نسخه‌ی محلی (کاملاً آفلاین) اجرا می‌شود.
- نسخه‌ی درون APK همان نسخه‌ی آخر ریلیز وب است؛ نسخه‌های بعدی خودکار نصب می‌شوند (بدون نصب دوباره APK).

## معماری / Architecture
| File | Role |
|---|---|
| `src/.../MainActivity.java` | Splash + WebView + immersive fullscreen |
| `src/.../GameServer.java` | Embedded HTTP server on `http://127.0.0.1:8777` (stable origin → localStorage persists) |
| `src/.../AndroidSources.java` | Serves updated `filesDir/game/` first, bundled `assets/game/` as fallback |
| `src/.../Updater.java` | Glue: GitHub Pages URLs, version read, progress callbacks |
| `src/.../UpdaterCore.java` | Pure-Java update engine: semver compare, SHA-256 verify, atomic writes |
| `tests/T.java` | Desktop-JVM unit tests (server + updater, fake remote) |
| `tests/TLive.java` | Live end-to-end test against real GitHub Pages |
| `build.sh` | Full build: aapt2 → ecj → d8 → zip → zipalign → apksigner |

## بیلد / Build
```bash
bash android/build.sh   # -> /home/z/my-project/download/GLM-FPS-Game-Android-1.0.0.apk
```
Tools: Android build-tools 33.0.2 + platform-33 android.jar + ecj (no Gradle, no Android Studio needed).

## امضا / Signing
Keystore: `android/keystore/glm-release.jks` (alias `glmfps`, pass `glmgame123`).
**هر APK آینده باید با همین keystore امضا شود** وگرنه اندروید آپدیت را قبول نمی‌کند.
(Future APKs MUST be signed with this same keystore or Android will refuse the update.)
