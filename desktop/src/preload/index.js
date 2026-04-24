"use strict";

const { contextBridge, ipcRenderer } = require("electron");
const MarkdownIt = require("markdown-it");

const md = new MarkdownIt({ html: false, linkify: true, breaks: true });

contextBridge.exposeInMainWorld("ts", {
  renderMarkdown: (text) => md.render(String(text || "")),
  escapeHtml: (text) => md.utils.escapeHtml(String(text || "")),
  // Auth
  getApiBaseUrl: () => ipcRenderer.invoke("auth:get-api-base-url"),
  getToken: () => ipcRenderer.invoke("auth:get-token"),
  saveToken: (token) => ipcRenderer.invoke("auth:save-token", token),
  logout: () => ipcRenderer.invoke("auth:logout"),
  openDashboard: () => ipcRenderer.invoke("auth:open-dashboard"),

  // Overlay
  triggerSolve: () => ipcRenderer.invoke("overlay:trigger-solve"),
  setClickThrough: (value) => ipcRenderer.invoke("overlay:set-click-through", value),
  getClickThrough: () => ipcRenderer.invoke("overlay:get-click-through"),
  hideOverlay: () => ipcRenderer.invoke("overlay:hide"),
  openExternal: (url) => ipcRenderer.invoke("overlay:open-external", url),

  // Subscriptions
  onSolveStarted: (cb) => {
    const handler = () => cb();
    ipcRenderer.on("overlay:solve-started", handler);
    return () => ipcRenderer.removeListener("overlay:solve-started", handler);
  },
  onSolveResult: (cb) => {
    const handler = (_evt, data) => cb(data);
    ipcRenderer.on("overlay:solve-result", handler);
    return () => ipcRenderer.removeListener("overlay:solve-result", handler);
  },
  onSolveError: (cb) => {
    const handler = (_evt, msg) => cb(msg);
    ipcRenderer.on("overlay:solve-error", handler);
    return () => ipcRenderer.removeListener("overlay:solve-error", handler);
  },
  onClickThroughChanged: (cb) => {
    const handler = (_evt, value) => cb(value);
    ipcRenderer.on("overlay:click-through-changed", handler);
    return () => ipcRenderer.removeListener("overlay:click-through-changed", handler);
  },
});
