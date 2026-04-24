"use strict";

(function () {
  const $body = document.getElementById("body");
  const $dot = document.getElementById("status-dot");
  const $statusText = document.getElementById("status-text");
  const $tokens = document.getElementById("tokens-label");
  const $solve = document.getElementById("btn-solve");
  const $clickthrough = document.getElementById("btn-clickthrough");
  const $hide = document.getElementById("btn-hide");
  const $logout = document.getElementById("btn-logout");

  function setStatus(kind, text) {
    $dot.className = `dot ${kind}`;
    $statusText.textContent = text;
  }

  function renderAnswer(answer, used_mock) {
    const html = window.ts.renderMarkdown(answer || "");
    $body.innerHTML =
      (used_mock
        ? `<div class="alert info">Backend returned a mock answer (no <code>GEMINI_API_KEY</code> on the server).</div>`
        : "") + html;
    // Open external links in default browser.
    $body.querySelectorAll("a[href^='http']").forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        window.ts.openExternal(a.getAttribute("href"));
      });
    });
  }

  $solve.addEventListener("click", () => window.ts.triggerSolve());
  $hide.addEventListener("click", () => window.ts.hideOverlay());
  $logout.addEventListener("click", () => window.ts.logout());

  $clickthrough.addEventListener("click", async () => {
    const cur = await window.ts.getClickThrough();
    const next = !cur;
    await window.ts.setClickThrough(next);
    $clickthrough.textContent = `Click: ${next ? "through" : "block"}`;
  });

  window.ts.getClickThrough().then((v) => {
    $clickthrough.textContent = `Click: ${v ? "through" : "block"}`;
  });

  window.ts.onSolveStarted(() => {
    setStatus("busy", "Capturing & solving…");
    $body.innerHTML = `<p class="muted">Capturing screen and asking the model. This usually takes 2–6 seconds…</p>`;
  });

  window.ts.onSolveResult((data) => {
    setStatus("ok", "Done");
    if (typeof data.tokens_remaining === "number") {
      $tokens.textContent = `Tokens left: ${data.tokens_remaining}`;
    }
    renderAnswer(data.answer || "(empty)", !!data.used_mock);
  });

  window.ts.onSolveError((msg) => {
    setStatus("err", "Error");
    $body.innerHTML = `<div class="alert error">${window.ts.escapeHtml(msg)}</div>`;
  });

  setStatus("idle", "Idle");
})();
