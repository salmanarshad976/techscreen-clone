# Tech Screen — Desktop

Cross-platform Electron app that wraps the Tech Screen replica with a real
"invisible" interview overlay: frameless, transparent, always-on-top, hidden
from screen-share where supported, with a global "Solve" hotkey that captures
the primary display and asks Google Gemini (vision) for an answer.

> Reminder: the original product is a third-party brand. This is a replica for
> educational/demo purposes. Don't ship as-is to end users.

## Features

- **Auth window** — register/login against the [shared FastAPI backend](https://techscreen-backend-fdnplevq.fly.dev). JWT is stored locally with `safeStorage` (OS keychain when available).
- **Overlay window** — frameless, transparent, always on top of every workspace including fullscreen apps, hidden from `screen-share` via `setContentProtection(true)` (macOS + recent Windows).
- **Click-through by default** — the overlay never blocks the underlying app/IDE. Toggle blocking on/off with `Ctrl/Cmd+Shift+M`.
- **Global hotkeys**
  - `Ctrl/Cmd+Shift+Space` — show / hide overlay
  - `Ctrl/Cmd+Shift+Enter` — capture primary display + ask the model
  - `Ctrl/Cmd+Shift+M` — toggle click-through
- **Capture pipeline** — uses Electron `desktopCapturer` to grab the primary display, hides the overlay during capture, sends a base64 PNG to the backend's `POST /api/solve` (Bearer auth, decrements one token per call).
- **LLM** — Gemini 2.0 Flash by default (vision-capable, generous free tier). Set `GEMINI_API_KEY` as a Fly secret on the backend; the key never ships in the desktop binary. Without a key the backend returns a deterministic mock so the full UI flow still works for demos.
- **Tray menu** — quick access to the overlay, click-through toggle, logout, and quit. App stays resident in the tray when all windows close.

## Run from source

```
cd desktop
npm install
npm start
```

By default the app calls the deployed backend. Override with:

```
TECHSCREEN_API_URL=http://127.0.0.1:8001 npm start
```

## Build installers

```
npm run dist:mac    # builds .dmg + .zip (run on macOS)
npm run dist:win    # builds .exe (NSIS) + portable .exe (run on Windows / wine)
npm run dist:linux  # builds .AppImage
```

The `Build Desktop Release` GitHub Actions workflow runs all three on push of a
tag like `desktop-v0.1.0`, attaches the artifacts to a GitHub Release, and is
the recommended way to get signed-in installers without owning macOS hardware.

## Why not Tauri?

Electron is the path of least resistance for `desktopCapturer` + global
shortcuts + cross-platform transparency / always-on-top. The bundle is bigger,
but the Electron primitives we depend on (`setContentProtection`,
`desktopCapturer`, `safeStorage`) all "just work". A Tauri rewrite is feasible
later if installer size matters.
