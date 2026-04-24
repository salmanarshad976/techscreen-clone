"use strict";

const path = require("path");
const {
  app,
  BrowserWindow,
  ipcMain,
  globalShortcut,
  desktopCapturer,
  screen,
  shell,
  safeStorage,
  Menu,
  Tray,
  nativeImage,
  Notification,
} = require("electron");

const fs = require("fs");
const os = require("os");

const isMac = process.platform === "darwin";

const DEFAULT_API_BASE_URL = "https://techscreen-backend-fdnplevq.fly.dev";
const API_BASE_URL = (process.env.TECHSCREEN_API_URL || DEFAULT_API_BASE_URL).replace(/\/$/, "");

// Auth/token persistence -------------------------------------------------------
const TOKEN_DIR = path.join(app.getPath("userData"));
const TOKEN_FILE = path.join(TOKEN_DIR, "session.token");

function saveToken(token) {
  try {
    fs.mkdirSync(TOKEN_DIR, { recursive: true });
    if (safeStorage.isEncryptionAvailable()) {
      const buf = safeStorage.encryptString(token);
      fs.writeFileSync(TOKEN_FILE, buf);
    } else {
      fs.writeFileSync(TOKEN_FILE, token, "utf8");
    }
  } catch (err) {
    console.error("saveToken failed", err);
  }
}

function loadToken() {
  try {
    if (!fs.existsSync(TOKEN_FILE)) return null;
    const data = fs.readFileSync(TOKEN_FILE);
    if (safeStorage.isEncryptionAvailable()) {
      try {
        return safeStorage.decryptString(data);
      } catch (e) {
        return null;
      }
    }
    return data.toString("utf8");
  } catch (err) {
    console.error("loadToken failed", err);
    return null;
  }
}

function clearToken() {
  try {
    if (fs.existsSync(TOKEN_FILE)) fs.unlinkSync(TOKEN_FILE);
  } catch (err) {
    console.error("clearToken failed", err);
  }
}

// Window management -----------------------------------------------------------
let authWindow = null;
let overlayWindow = null;
let tray = null;
let overlayClickThrough = true;

function createAuthWindow() {
  if (authWindow && !authWindow.isDestroyed()) {
    authWindow.show();
    authWindow.focus();
    return authWindow;
  }
  authWindow = new BrowserWindow({
    width: 480,
    height: 640,
    resizable: false,
    minimizable: true,
    maximizable: false,
    fullscreenable: false,
    title: "Tech Screen",
    backgroundColor: "#000000",
    webPreferences: {
      preload: path.join(__dirname, "..", "preload", "index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });
  authWindow.removeMenu();
  authWindow.loadFile(path.join(__dirname, "..", "renderer", "auth.html"));
  authWindow.on("closed", () => {
    authWindow = null;
  });
  return authWindow;
}

function createOverlayWindow() {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.show();
    overlayWindow.focus();
    return overlayWindow;
  }
  const display = screen.getPrimaryDisplay();
  const { width: dw, height: dh } = display.workAreaSize;
  const w = Math.min(560, Math.floor(dw * 0.4));
  const h = Math.min(720, Math.floor(dh * 0.7));
  const x = display.workArea.x + dw - w - 24;
  const y = display.workArea.y + 24;

  overlayWindow = new BrowserWindow({
    x,
    y,
    width: w,
    height: h,
    frame: false,
    transparent: true,
    backgroundColor: "#00000000",
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: true,
    movable: true,
    hasShadow: false,
    fullscreenable: false,
    focusable: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "..", "preload", "index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      backgroundThrottling: false,
    },
  });
  overlayWindow.setAlwaysOnTop(true, "screen-saver");
  overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

  // Hide from screen capture/screen-share where supported (macOS, modern Windows).
  try {
    overlayWindow.setContentProtection(true);
  } catch (e) {
    // ignored
  }

  // Start in click-through mode so it doesn't block the underlying app/IDE.
  overlayClickThrough = true;
  overlayWindow.setIgnoreMouseEvents(true, { forward: true });

  overlayWindow.removeMenu();
  overlayWindow.loadFile(path.join(__dirname, "..", "renderer", "overlay.html"));
  overlayWindow.once("ready-to-show", () => overlayWindow.show());
  overlayWindow.on("closed", () => {
    overlayWindow = null;
  });
  return overlayWindow;
}

function showOverlay() {
  if (!overlayWindow || overlayWindow.isDestroyed()) {
    createOverlayWindow();
  } else {
    overlayWindow.show();
  }
}

function toggleOverlayVisibility() {
  if (!overlayWindow || overlayWindow.isDestroyed()) {
    createOverlayWindow();
    return;
  }
  if (overlayWindow.isVisible()) {
    overlayWindow.hide();
  } else {
    overlayWindow.show();
  }
}

function toggleClickThrough() {
  if (!overlayWindow || overlayWindow.isDestroyed()) return;
  overlayClickThrough = !overlayClickThrough;
  overlayWindow.setIgnoreMouseEvents(overlayClickThrough, { forward: true });
  overlayWindow.webContents.send("overlay:click-through-changed", overlayClickThrough);
}

// Tray ------------------------------------------------------------------------
function buildTrayIcon() {
  // Render a simple 16x16 green dot via nativeImage from a base64 PNG so we
  // don't need to ship a real icon during dev.
  const png = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAQElEQVR42mNk+M9QzwAEjA" +
      "wMDAxQAEMM/0EJsAB8DGNCYqGCxgYqIBpAYqAFAEYwoBhgZGcEsBiYGAAAJxgEZgcZsr" +
      "wAAAAASUVORK5CYII=",
    "base64",
  );
  return nativeImage.createFromBuffer(png);
}

function createTray() {
  if (tray) return tray;
  try {
    tray = new Tray(buildTrayIcon());
  } catch (e) {
    return null;
  }
  tray.setToolTip("Tech Screen");
  const refresh = () =>
    tray.setContextMenu(
      Menu.buildFromTemplate([
        { label: "Show overlay", click: () => showOverlay() },
        { label: "Toggle visibility (Ctrl/Cmd+Shift+Space)", click: () => toggleOverlayVisibility() },
        {
          label: overlayClickThrough
            ? "Allow clicks on overlay (Ctrl/Cmd+Shift+M)"
            : "Make overlay click-through (Ctrl/Cmd+Shift+M)",
          click: () => {
            toggleClickThrough();
            refresh();
          },
        },
        { label: "Solve now (Ctrl/Cmd+Shift+Enter)", click: () => triggerSolve() },
        { type: "separator" },
        {
          label: "Logout",
          click: () => {
            clearToken();
            if (overlayWindow && !overlayWindow.isDestroyed()) overlayWindow.close();
            createAuthWindow();
          },
        },
        { label: "Quit", click: () => app.quit() },
      ]),
    );
  refresh();
  return tray;
}

// Screen capture --------------------------------------------------------------
async function capturePrimaryDisplayBase64() {
  const display = screen.getPrimaryDisplay();
  // Hide the overlay during capture so it isn't in the screenshot.
  let wasVisible = false;
  if (overlayWindow && !overlayWindow.isDestroyed() && overlayWindow.isVisible()) {
    wasVisible = true;
    overlayWindow.hide();
    // Give the compositor a beat so the overlay is gone before we grab.
    await new Promise((resolve) => setTimeout(resolve, 120));
  }
  try {
    const sources = await desktopCapturer.getSources({
      types: ["screen"],
      thumbnailSize: {
        width: Math.min(2560, display.size.width),
        height: Math.min(1600, display.size.height),
      },
    });
    if (!sources.length) throw new Error("No screen sources available");
    // Prefer the source matching the primary display.id when available.
    const primaryId = String(display.id);
    const chosen =
      sources.find((s) => s.display_id && String(s.display_id) === primaryId) ||
      sources[0];
    const png = chosen.thumbnail.toPNG();
    return png.toString("base64");
  } finally {
    if (wasVisible && overlayWindow && !overlayWindow.isDestroyed()) {
      overlayWindow.show();
    }
  }
}

async function triggerSolve() {
  const token = loadToken();
  if (!token) {
    if (Notification.isSupported()) {
      new Notification({ title: "Tech Screen", body: "Please log in first." }).show();
    }
    createAuthWindow();
    return;
  }
  if (!overlayWindow || overlayWindow.isDestroyed()) createOverlayWindow();
  showOverlay();
  overlayWindow.webContents.send("overlay:solve-started");
  let imageBase64;
  try {
    imageBase64 = await capturePrimaryDisplayBase64();
  } catch (err) {
    overlayWindow.webContents.send("overlay:solve-error", `Capture failed: ${err.message}`);
    return;
  }
  try {
    const resp = await fetch(`${API_BASE_URL}/api/solve`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ image_base64: imageBase64 }),
    });
    if (!resp.ok) {
      let detail = `${resp.status} ${resp.statusText}`;
      try {
        const j = await resp.json();
        if (j && j.detail) detail = `${resp.status}: ${j.detail}`;
      } catch (_) {}
      overlayWindow.webContents.send("overlay:solve-error", detail);
      return;
    }
    const data = await resp.json();
    overlayWindow.webContents.send("overlay:solve-result", data);
  } catch (err) {
    overlayWindow.webContents.send("overlay:solve-error", err.message);
  }
}

// IPC -------------------------------------------------------------------------
ipcMain.handle("auth:get-api-base-url", () => API_BASE_URL);

ipcMain.handle("auth:get-token", () => loadToken());

ipcMain.handle("auth:save-token", (_evt, token) => {
  if (typeof token !== "string" || !token) return false;
  saveToken(token);
  return true;
});

ipcMain.handle("auth:logout", () => {
  clearToken();
  if (overlayWindow && !overlayWindow.isDestroyed()) overlayWindow.close();
  createAuthWindow();
  return true;
});

ipcMain.handle("auth:open-dashboard", () => {
  if (authWindow && !authWindow.isDestroyed()) authWindow.close();
  createOverlayWindow();
  return true;
});

ipcMain.handle("overlay:trigger-solve", () => triggerSolve());

ipcMain.handle("overlay:set-click-through", (_evt, value) => {
  if (!overlayWindow || overlayWindow.isDestroyed()) return false;
  overlayClickThrough = !!value;
  overlayWindow.setIgnoreMouseEvents(overlayClickThrough, { forward: true });
  return overlayClickThrough;
});

ipcMain.handle("overlay:get-click-through", () => overlayClickThrough);

ipcMain.handle("overlay:hide", () => {
  if (overlayWindow && !overlayWindow.isDestroyed()) overlayWindow.hide();
  return true;
});

ipcMain.handle("overlay:open-external", (_evt, url) => shell.openExternal(url));

// Lifecycle -------------------------------------------------------------------
function registerShortcuts() {
  globalShortcut.register("CommandOrControl+Shift+Space", () => toggleOverlayVisibility());
  globalShortcut.register("CommandOrControl+Shift+Enter", () => triggerSolve());
  globalShortcut.register("CommandOrControl+Shift+M", () => toggleClickThrough());
}

app.whenReady().then(() => {
  if (isMac) app.dock?.hide?.();
  createTray();
  registerShortcuts();
  const token = loadToken();
  if (token) {
    createOverlayWindow();
  } else {
    createAuthWindow();
  }

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      const t = loadToken();
      if (t) createOverlayWindow();
      else createAuthWindow();
    }
  });
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});

app.on("window-all-closed", (e) => {
  // Keep running in the tray on macOS; on Windows/Linux, allow clean exit
  // unless the tray is alive (we keep the app resident).
  if (tray) {
    e?.preventDefault?.();
    return;
  }
  if (!isMac) app.quit();
});
