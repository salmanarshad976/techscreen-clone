"use strict";

(function () {
  const tabs = document.querySelectorAll(".auth-tab");
  const formLogin = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");
  const alertEl = document.getElementById("alert");

  let apiBase = "";
  window.ts.getApiBaseUrl().then((u) => {
    apiBase = u;
  });

  function showAlert(kind, text) {
    alertEl.className = `alert ${kind}`;
    alertEl.textContent = text;
    alertEl.style.display = "block";
  }
  function clearAlert() {
    alertEl.style.display = "none";
    alertEl.textContent = "";
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const which = tab.dataset.tab;
      formLogin.style.display = which === "login" ? "block" : "none";
      formRegister.style.display = which === "register" ? "block" : "none";
      clearAlert();
    });
  });

  async function postJson(path, body) {
    const resp = await fetch(`${apiBase}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let json = null;
    try {
      json = await resp.json();
    } catch (_) {}
    if (!resp.ok) {
      const detail =
        (json && json.detail) || `${resp.status} ${resp.statusText}`;
      throw new Error(detail);
    }
    return json;
  }

  formLogin.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAlert();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    try {
      const data = await postJson("/api/auth/login", { email, password });
      await window.ts.saveToken(data.access_token);
      showAlert("info", "Logged in. Opening overlay…");
      setTimeout(() => window.ts.openDashboard(), 250);
    } catch (err) {
      showAlert("error", err.message);
    }
  });

  formRegister.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAlert();
    const full_name = document.getElementById("reg-name").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;
    try {
      const data = await postJson("/api/auth/register", {
        email,
        password,
        full_name,
      });
      await window.ts.saveToken(data.access_token);
      showAlert("info", "Account created. Opening overlay…");
      setTimeout(() => window.ts.openDashboard(), 250);
    } catch (err) {
      showAlert("error", err.message);
    }
  });
})();
