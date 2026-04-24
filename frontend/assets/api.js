/* Tiny API client for the Tech Screen replica frontend. */
(function () {
  const DEFAULT_API_BASE =
    location.hostname === "localhost" || location.hostname === "127.0.0.1"
      ? "http://127.0.0.1:8001"
      : "https://techscreen-backend-fdnplevq.fly.dev";

  const API_BASE = window.__TECHSCREEN_API_BASE__ || DEFAULT_API_BASE;
  const TOKEN_KEY = "techscreen.token";

  async function request(path, { method = "GET", body, auth = false } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth) {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    let data = null;
    try {
      data = await res.json();
    } catch {
      // ignore
    }
    if (!res.ok) {
      const detail =
        (data && (data.detail || data.message)) || res.statusText || "Request failed";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return data;
  }

  const TechScreenAPI = {
    apiBase: API_BASE,
    isLoggedIn() {
      return !!localStorage.getItem(TOKEN_KEY);
    },
    setToken(token) {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    },
    logout() {
      localStorage.removeItem(TOKEN_KEY);
    },
    register(email, password, fullName) {
      return request("/api/auth/register", {
        method: "POST",
        body: { email, password, full_name: fullName || "" },
      });
    },
    login(email, password) {
      return request("/api/auth/login", {
        method: "POST",
        body: { email, password },
      });
    },
    me() {
      return request("/api/me", { auth: true });
    },
    dashboard() {
      return request("/api/dashboard", { auth: true });
    },
    consumeToken() {
      return request("/api/dashboard/consume-token", {
        method: "POST",
        auth: true,
      });
    },
  };

  window.TechScreenAPI = TechScreenAPI;
})();
