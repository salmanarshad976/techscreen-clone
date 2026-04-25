const API_BASE = window.__FL_API_BASE__ ||
  (location.hostname === "localhost" || location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8001"
    : "");

const api = {
  token: localStorage.getItem("fl_token"),
  user: JSON.parse(localStorage.getItem("fl_user") || "null"),

  async _fetch(path, opts = {}) {
    const headers = { "Content-Type": "application/json", ...opts.headers };
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;
    const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
    if (res.status === 401) { this.logout(); return; }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(err.detail || "Request failed");
    }
    return res.json();
  },

  async register(email, password, full_name) {
    const data = await this._fetch("/api/auth/register", {
      method: "POST", body: JSON.stringify({ email, password, full_name }),
    });
    this.token = data.access_token;
    this.user = data.user;
    localStorage.setItem("fl_token", data.access_token);
    localStorage.setItem("fl_user", JSON.stringify(data.user));
    return data;
  },

  async login(email, password) {
    const data = await this._fetch("/api/auth/login", {
      method: "POST", body: JSON.stringify({ email, password }),
    });
    this.token = data.access_token;
    this.user = data.user;
    localStorage.setItem("fl_token", data.access_token);
    localStorage.setItem("fl_user", JSON.stringify(data.user));
    return data;
  },

  logout() {
    this.token = null; this.user = null;
    localStorage.removeItem("fl_token");
    localStorage.removeItem("fl_user");
    window.location.href = "/login.html";
  },

  isLoggedIn() { return !!this.token; },

  getMe() { return this._fetch("/api/me"); },
  getDashboard() { return this._fetch("/api/dashboard"); },
  searchLeads(niche, location) {
    return this._fetch("/api/search", { method: "POST", body: JSON.stringify({ niche, location }) });
  },
  getSearchResults(id) { return this._fetch(`/api/search/${id}`); },
  bulkSearch(niche, cities) {
    return this._fetch("/api/bulk-search", { method: "POST", body: JSON.stringify({ niche, cities }) });
  },
  nicheScan(niches, cities, service_type) {
    return this._fetch("/api/niche-scan", { method: "POST", body: JSON.stringify({ niches, cities, service_type }) });
  },
  serpAnalyze(query, location) {
    return this._fetch("/api/serp", { method: "POST", body: JSON.stringify({ query, location }) });
  },
  competitorCompare(url1, url2) {
    return this._fetch("/api/competitor-compare", { method: "POST", body: JSON.stringify({ url1, url2 }) });
  },
  napAudit(business_name, address, phone) {
    return this._fetch("/api/nap-audit", { method: "POST", body: JSON.stringify({ business_name, address, phone }) });
  },
  backlinks(domain) {
    return this._fetch("/api/backlinks", { method: "POST", body: JSON.stringify({ domain }) });
  },
  generatePitch(lead_id, tone) {
    return this._fetch("/api/pitch", { method: "POST", body: JSON.stringify({ lead_id, tone }) });
  },
  saveLead(lead_id) {
    return this._fetch(`/api/leads/${lead_id}/save`, { method: "POST" });
  },
  unsaveLead(lead_id) {
    return this._fetch(`/api/leads/${lead_id}/save`, { method: "DELETE" });
  },
  updateStage(lead_id, stage) {
    return this._fetch(`/api/leads/${lead_id}/stage`, { method: "PUT", body: JSON.stringify({ lead_id, stage }) });
  },
  getPipeline() { return this._fetch("/api/pipeline"); },
  createProposal(title, client_name, lead_id) {
    return this._fetch("/api/proposals", { method: "POST", body: JSON.stringify({ title, client_name, lead_id }) });
  },
  getProposals() { return this._fetch("/api/proposals"); },
  createCampaign(name) {
    return this._fetch("/api/campaigns", { method: "POST", body: JSON.stringify({ name }) });
  },
  getCampaigns() { return this._fetch("/api/campaigns"); },
  createTemplate(name, subject, body, category) {
    return this._fetch("/api/templates", { method: "POST", body: JSON.stringify({ name, subject, body, category }) });
  },
  getTemplates() { return this._fetch("/api/templates"); },
  createCaseStudy(title, client_name, description, before_metrics, after_metrics) {
    return this._fetch("/api/case-studies", { method: "POST", body: JSON.stringify({ title, client_name, description, before_metrics, after_metrics }) });
  },
  getCaseStudies() { return this._fetch("/api/case-studies"); },
  roiCalculate(monthly_revenue, current_traffic, projected_traffic_increase, conversion_rate) {
    return this._fetch("/api/roi-calculate", { method: "POST", body: JSON.stringify({ monthly_revenue, current_traffic, projected_traffic_increase, conversion_rate }) });
  },
  generateWebsite(business_name, niche, location, phone, description) {
    return this._fetch("/api/generate-website", { method: "POST", body: JSON.stringify({ business_name, niche, location, phone, description }) });
  },
  rankTracking(domain, keywords, location) {
    return this._fetch("/api/rank-tracking", { method: "POST", body: JSON.stringify({ domain, keywords, location }) });
  },
  linkHealth(domain) {
    return this._fetch("/api/link-health", { method: "POST", body: JSON.stringify({ domain }) });
  },
};
