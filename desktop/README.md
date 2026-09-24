# GLM FPS Game — Windows Desktop Edition

بسته‌بندی بازی به‌صورت برنامه ویندوزی (کاملاً آفلاین) با نصب‌کننده NSIS.

## ساختار

```
desktop/
  app/main.js            Electron main process (window, F11 fullscreen, no reload)
  app/package.json       Electron runtime manifest
  app/app-icon.png/ico   آیکون برنامه و نصب‌کننده
  build/installer.nsi    اسکریپت نصب‌کننده (فارسی + انگلیسی)
  build/build.sh         اسکریپت ساخت روی لینوکس (بدون نیاز به root)
```

## Build (Linux)

```bash
# one-time: portable makensis (Debian debs, extracted without root)
# see /home/z/my-project/scripts/fetch_nsis_debs.py
./build/build.sh
# -> dist/GLM-FPS-Game-Setup-1.0.0.exe
```

## Installer features

- زبان نصب: فارسی / انگلیسی
- انتخاب پوشه نصب (پیش‌فرض: `%LOCALAPPDATA%\Programs\GLMFPSGame`، بدون نیاز به ادمین)
- چک‌باکس میان‌بر دسکتاپ و منوی استارت
- اجرای بازی بعد از نصب + Uninstall از Control Panel
- Electron 22 (Chromium 108) — سازگار با Windows 7/8/10/11

## Smoke test (Linux)

```bash
GLM_SMOKE=1 xvfb-run -a node_modules/.bin/electron --no-sandbox \
  desktop/staging/app-root/resources/app
# expect: "[smoke] did-finish-load url=file://.../game/fps-game.html"
```

> Note: the packaged game content is copied from the repo root at build time
> (`fps-game.html` + `fps-game-assets/`), so desktop builds always match the
> current web version.
