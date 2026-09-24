// GLM FPS Game - Electron main process (desktop edition)
const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');

const GAME_FILE = path.join(__dirname, 'game', 'fps-game.html');
const IS_SMOKE = process.env.GLM_SMOKE === '1';

let win = null;

function createWindow () {
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
  win.loadFile(GAME_FILE);

  win.once('ready-to-show', () => { win.show(); });

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

app.whenReady().then(() => {
  app.setAppUserModelId('com.aydinbarzegary.glmfpsgame');
  createWindow();
  if (IS_SMOKE) {
    setTimeout(() => { console.log('[smoke] done'); app.quit(); }, 8000);
  }
});

app.on('window-all-closed', () => app.quit());
