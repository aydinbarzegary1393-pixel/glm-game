// GLM FPS Game - Electron main process (desktop edition v1.1.0)
// Boot flow: splash -> check GitHub for a newer release (version.json manifest)
//   -> download changed files (SHA-256 verified) -> launch the game.
// No internet / any failure -> the already-installed game launches anyway.
const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const fs = require('fs');
const { checkAndUpdate } = require('./updater');

const IS_SMOKE = process.env.GLM_SMOKE === '1';
const UPDATE_ENABLED = process.env.GLM_NO_UPDATE !== '1';

if (process.env.GLM_USER_DATA_DIR) app.setPath('userData', process.env.GLM_USER_DATA_DIR);

let splash = null;
let win = null;

// ---------- game locations ----------
function findBundledGame () {
  const packaged = path.join(__dirname, 'game');                    // resources/app/game (installer layout)
  if (fs.existsSync(path.join(packaged, 'fps-game.html'))) return packaged;
  const repoRoot = path.join(__dirname, '..', '..');                // dev: repo root (fps-game.html + fps-game-assets/)
  if (fs.existsSync(path.join(repoRoot, 'fps-game.html'))) return repoRoot;
  return packaged;
}

function copyBundledGame (srcDir, dstDir) {
  fs.mkdirSync(dstDir, { recursive: true });
  try { fs.copyFileSync(path.join(srcDir, 'fps-game.html'), path.join(dstDir, 'fps-game.html')); } catch (e) {}
  try {
    const assets = path.join(srcDir, 'fps-game-assets');
    if (fs.existsSync(assets)) fs.cpSync(assets, path.join(dstDir, 'fps-game-assets'), { recursive: true });
  } catch (e) {}
  try {
    const ver = path.join(srcDir, 'version.json');
    if (fs.existsSync(ver)) fs.copyFileSync(ver, path.join(dstDir, 'version.json'));
  } catch (e) {}
}

// Seed the writable game dir from the bundled copy so that:
//  - first run works fully offline (bundled = the installer's copy)
//  - hash-compare can skip already-current files on later updates
function seedGameDir () {
  const gameDir = path.join(app.getPath('userData'), 'game');
  const bundled = findBundledGame();
  if (!fs.existsSync(path.join(gameDir, 'version.json'))) {
    try {
      copyBundledGame(bundled, gameDir);
      console.log('[boot] seeded game dir from ' + bundled);
    } catch (e) {
      console.error('[boot] seed failed: ' + e.message);
    }
  }
  return { gameDir, bundled };
}

// ---------- splash (update status) ----------
const SPLASH_HTML = '<!doctype html><html><head><meta charset="utf-8"><style>' +
  'body{margin:0;background:#0b0f0c;color:#cfe3d4;font-family:"Segoe UI",Tahoma,Vazirmatn,sans-serif;' +
  'display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;user-select:none}' +
  'h1{font-size:22px;margin:14px 0 2px;color:#8fe3a2;letter-spacing:1px}' +
  '#fa{font-size:14px;margin:8px 0 2px}#en{font-size:12px;opacity:.65;margin:2px 0 16px}' +
  '#barbox{width:290px;height:7px;background:#1c2a20;border-radius:4px;overflow:hidden}' +
  '#bar{height:100%;width:0%;background:#4caf6d;border-radius:4px;transition:width .15s}' +
  '</style></head><body>' +
  '<h1>GLM FPS GAME</h1>' +
  '<div id="fa"></div><div id="en"></div>' +
  '<div id="barbox"><div id="bar"></div></div>' +
  '<script>function setStatus(fa,en,pct){document.getElementById("fa").textContent=fa;' +
  'document.getElementById("en").textContent=en;' +
  'document.getElementById("bar").style.width=(pct==null?0:Math.round(pct))+"%";}</script>' +
  '</body></html>';

function setSplash (fa, en, pct) {
  if (splash && !splash.isDestroyed()) {
    try { splash.webContents.executeJavaScript('setStatus(' + JSON.stringify(fa) + ',' + JSON.stringify(en) + ',' + JSON.stringify(pct == null ? null : pct) + ')'); } catch (e) {}
  }
}

function createSplash () {
  splash = new BrowserWindow({
    width: 460,
    height: 280,
    frame: false,
    resizable: false,
    alwaysOnTop: true,
    show: true,
    backgroundColor: '#0b0f0c',
    center: true,
    title: 'GLM FPS Game',
    webPreferences: { nodeIntegration: false, contextIsolation: true, spellcheck: false }
  });
  splash.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(SPLASH_HTML));
  setSplash('در حال آماده‌سازی…', 'Preparing…', null);
}

// ---------- main window (unchanged behavior from v1.0.0) ----------
function createWindow (gameFile) {
  win = new BrowserWindow({
    width: 1366,
    height: 768,
    minWidth: 900,
    minHeight: 540,
    show: false,
    backgroundColor: '#000000',
    autoHideMenuBar: true,
    title: 'GLM FPS Game',
    icon: path.join(__dirname, 'app-icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      spellcheck: false,
      backgroundThrottling: false
    }
  });

  Menu.setApplicationMenu(null);
  win.loadFile(gameFile);

  win.once('ready-to-show', () => {
    if (splash && !splash.isDestroyed()) splash.close();
    win.show();
  });

  win.webContents.on('did-finish-load', () => {
    console.log('[smoke] did-finish-load url=' + win.webContents.getURL());
  });
  win.webContents.on('did-fail-load', (_e, code, desc, url) => {
    console.error('[smoke] did-fail-load code=' + code + ' desc=' + desc + ' url=' + url);
  });
  win.webContents.on('render-process-gone', (_e, details) => {
    console.error('[smoke] render-process-gone reason=' + details.reason);
  });
  if (IS_SMOKE) {
    win.webContents.on('console-message', (_e, level, message, line, sourceId) => {
      console.log('[page-console] L' + level + ' ' + message + ' (' + sourceId + ':' + line + ')');
    });
  }

  // no popups / external navigation
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (e, url) => {
    if (!url.startsWith('file://')) e.preventDefault();
  });

  // F11 fullscreen toggle, block accidental Ctrl+R reload mid-game
  win.webContents.on('before-input-event', (e, input) => {
    if (input.type !== 'keyDown') return;
    if (input.key === 'F11') {
      win.setFullScreen(!win.isFullScreen());
      e.preventDefault();
    } else if ((input.control || input.meta) && (input.key === 'r' || input.key === 'R')) {
      e.preventDefault();
    }
  });
}

// ---------- update status texts (bilingual) ----------
function splashTexts (res) {
  if (!res) return ['در حال بررسی به‌روزرسانی…', 'Checking for updates…', null];
  if (res.phase === 'check') return ['بررسی نسخه جدید…', 'Checking for updates…', null];
  if (res.phase === 'download') {
    const done = (res.downloaded || 0) + (res.skipped || 0);
    const total = res.total || 1;
    return ['در حال دریافت نسخه جدید… (' + done + '/' + total + ')', 'Downloading update… (' + done + '/' + total + ')', (done / total) * 100];
  }
  if (res.phase === 'offline') return ['اینترنت در دسترس نیست — اجرای بازی…', 'Offline — launching game…', 100];
  if (res.phase === 'error') return ['به‌روزرسانی خودکار ممکن نشد — اجرای بازی…', 'Update failed — launching game…', 100];
  if (res.phase === 'done' && res.updated) return ['به‌روزرسانی انجام شد — اجرای بازی…', 'Updated — launching game…', 100];
  if (res.phase === 'done') return ['بازی به‌روز است — اجرا…', 'Up to date — launching…', 100];
  return ['در حال اجرا…', 'Launching…', null];
}

async function boot () {
  app.setAppUserModelId('com.aydinbarzegary.glmfpsgame');
  createSplash();

  const { gameDir, bundled } = seedGameDir();
  const entry = path.join(gameDir, 'fps-game.html');
  let launchFile = fs.existsSync(entry) ? entry : path.join(bundled, 'fps-game.html');

  if (UPDATE_ENABLED) {
    let lastTick = 0;
    const res = await checkAndUpdate({
      gameDir: gameDir,
      onProgress: (p) => {
        const [fa, en, pct] = splashTexts(p);
        const now = Date.now();
        if (p.phase === 'download' && now - lastTick < 90) return; // throttle UI
        lastTick = now;
        setSplash(fa, en, pct);
      }
    });
    console.log('[update] ' + JSON.stringify(res));
    if (res.status === 'updated' && fs.existsSync(entry)) {
      // relaunch point: use freshly updated files
      launchFile = entry;
    }
    const [fa, en, pct] = splashTexts({ phase: 'done', updated: res.status === 'updated' });
    setSplash(fa, en, pct);
  } else {
    console.log('[update] disabled by GLM_NO_UPDATE=1');
  }

  createWindow(launchFile);
  if (IS_SMOKE) {
    setTimeout(() => { console.log('[smoke] done'); app.quit(); }, 8000);
  }
}

app.whenReady().then(boot);
app.on('window-all-closed', () => app.quit());
