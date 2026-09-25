# GLM FPS Game — Windows Desktop Edition

بسته‌بندی بازی به‌صورت برنامه ویندوزی با نصب‌کننده NSIS + **آپدیت خودکار از GitHub**.

## آپدیت خودکار (v1.1.0)

هر بار بازی اجرا شود:

1. **اینترنت دارد؟** → مانیفست `version.json` از GitHub Pages چک می‌شود (همان مانیفستی که APK اندروید استفاده می‌کند): شماره نسخه + SHA-256 + حجم تک‌تک فایل‌های بازی
2. **ریلیز جدیدتر منتشر شده؟** → فقط فایل‌های تغییرکرده دانلود می‌شوند (اسپلش با نوار پیشرفت)، هش هر فایل تأیید و اتمیک جایگزین می‌شود؛ `version.json` آخر از همه نوشته می‌شود تا اگر وسط کار قطع شد، نسخه قبلی سالم بماند
3. **تمام شد؟** → بازی اجرا می‌شود
4. **اینترنت ندارد یا هر خطایی؟** → بدون معطلی از کپی لوکال اجرا می‌شود (نصب‌کننده همیشه یک نسخه کامل آفلاین داخل خودش دارد)

محل بازی به‌روزشده: `%APPDATA%\glm-fps-game\game` (نوشتنی، بدون نیاز به ادمین — کپی اولیه از محل نصب seed می‌شود).

## ساختار

```
desktop/
  app/main.js            Electron main process (splash + updater + window, F11, no reload)
  app/updater.js         موتور آپدیت خالص Node (چک مانیفست، دانلود تغییرات، sha256، اتمیک)
  app/package.json       Electron runtime manifest
  app/app-icon.png/ico   آیکون برنامه و نصب‌کننده
  build/installer.nsi    اسکریپت نصب‌کننده (فارسی + انگلیسی)
  build/build.sh         اسکریپت ساخت روی لینوکس (بدون نیاز به root)
```

## Build (Linux)

```bash
# one-time: portable makensis (Debian debs nsis_3.12-1_amd64 + nsis-common, dpkg -x)
./build/build.sh
# -> dist/GLM-FPS-Game-Setup-1.1.0.exe
```

## Installer features

- زبان نصب: فارسی / انگلیسی
- انتخاب پوشه نصب (پیش‌فرض: `%LOCALAPPDATA%\Programs\GLMFPSGame`، بدون نیاز به ادمین)
- چک‌باکس میان‌بر دسکتاپ و منوی استارت
- اجرای بازی بعد از نصب + Uninstall از Control Panel
- Electron 22 (Chromium 108) — سازگار با Windows 7/8/10/11

## Tests

- `scripts/test_desktop_updater.js` — ۳۶ تست Node: semver، آفلاین، سینک کامل، ریران صفر دانلود، تعمیر تک‌فایل، هش دستکاری‌شده، path traversal، سینک زنده GitHub Pages
- سموک Electron روی Xvfb (لینوکس): آنلاین/آفلاین/آپدیت واقعی از نسخه قدیمی — هر سه حالت بازی را لود می‌کند

```bash
GLM_SMOKE=1 GLM_USER_DATA_DIR=/tmp/ud1 xvfb-run -a electron desktop/app
# expect: "[update] {...}" + "[smoke] did-finish-load url=file://.../game/fps-game.html"
```

> Note: the packaged game content is copied from the repo root at build time
> (`fps-game.html` + `fps-game-assets/` + `version.json`), so desktop builds always
> match the current web version. For every future game release, regenerate
> `version.json` (scripts/gen_version_manifest.py) BEFORE committing — otherwise
> desktop + Android updaters won't see the update.
