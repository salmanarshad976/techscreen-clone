// ── Guard ──
if (!api.isLoggedIn()) { window.location.href = "login.html"; }

let currentResults = [];
let currentFilter = "all";
let dashboardData = null;

// ── Navigation ──
function navigate(page) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".sidebar-link").forEach(l => l.classList.remove("active"));
  const el = document.getElementById("page-" + page);
  if (el) el.classList.add("active");
  const link = document.querySelector(`[data-page="${page}"]`);
  if (link) link.classList.add("active");
  const names = {
    dashboard:"Dashboard", search:"Search Leads", "bulk-search":"Bulk City Search",
    "niche-scanner":"Niche Scanner", "tech-discovery":"Tech Discovery", serp:"SERP Analyzer",
    "nap-audit":"NAP Citation Audit", backlinks:"Backlink Finder", "backlink-monitoring":"Backlink Monitoring",
    "rank-tracking":"Rank Tracking", "link-health":"Link Health", pipeline:"Leads & Pipeline",
    "competitor-compare":"Competitor Compare", proposals:"Proposals", "case-studies":"Case Studies",
    "roi-calculator":"ROI Calculator", inbox:"Inbox", campaigns:"Campaigns", templates:"Template Library",
    "review-templates":"Review Templates", deliverability:"Deliverability", websites:"AI Websites",
    portfolio:"My Portfolio", billing:"Billing", settings:"Settings",
  };
  document.getElementById("breadcrumb").textContent = names[page] || page;
  if (page === "pipeline") loadPipeline();
  if (page === "proposals") loadProposals();
  if (page === "campaigns") loadCampaigns();
  if (page === "templates") loadTemplates();
  if (page === "case-studies") loadCaseStudies();
  if (page === "settings") loadSettings();
  window.location.hash = page;
}

// ── Init ──
async function init() {
  try {
    dashboardData = await api.getDashboard();
    const user = api.user;
    document.getElementById("userName").textContent = user.full_name;
    document.getElementById("userPlan").textContent = capitalize(user.plan) + " Plan";
    document.getElementById("userAvatar").textContent = getInitials(user.full_name);
    document.getElementById("usageText").textContent = `${dashboardData.searches_used} / ${dashboardData.searches_limit} searches`;
    document.getElementById("welcomeTitle").textContent = `Welcome back, ${user.full_name.split(" ")[0]}!`;
    document.getElementById("welcomeSubtitle").textContent = `${dashboardData.saved_leads} leads saved · ${dashboardData.searches_used}/${dashboardData.searches_limit} searches this month`;
    document.getElementById("statSearches").textContent = `${dashboardData.searches_used} / ${dashboardData.searches_limit}`;
    document.getElementById("searchProgress").style.width = `${(dashboardData.searches_used / dashboardData.searches_limit) * 100}%`;
    document.getElementById("statLeads").textContent = dashboardData.saved_leads;
    document.getElementById("statPitches").textContent = dashboardData.pitches_sent;
    if (dashboardData.plan !== "free") document.getElementById("upgradeBar").style.display = "none";

    if (dashboardData.recent_searches && dashboardData.recent_searches.length > 0) {
      const el = document.getElementById("recentSearches");
      el.innerHTML = dashboardData.recent_searches.map(s => `
        <div class="card" style="margin-bottom:8px;cursor:pointer;" onclick="loadPreviousSearch(${s.id})">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div><strong>${s.niche}</strong> in ${s.location} <span style="color:var(--text-muted);font-size:0.8rem;">— ${s.result_count} results</span></div>
            <span style="font-size:0.75rem;color:var(--text-muted);">${timeAgo(s.created_at)}</span>
          </div>
        </div>
      `).join("");
    }
  } catch (e) { console.error(e); }

  const hash = window.location.hash.replace("#", "");
  if (hash) navigate(hash); else navigate("dashboard");
}

// ── Search Leads ──
async function doSearch() {
  const niche = document.getElementById("searchNiche").value.trim();
  const location = document.getElementById("searchLocation").value.trim();
  if (!niche || !location) return showToast("Enter both a niche and location", "error");

  document.getElementById("searchLoading").style.display = "flex";
  document.getElementById("searchResults").style.display = "none";
  document.getElementById("searchBtn").disabled = true;

  try {
    const data = await api.searchLeads(niche, location);
    currentResults = data.results;
    document.getElementById("resultCount").textContent = `${data.total} businesses found`;
    renderFilters(data);
    renderResults(currentResults);
    document.getElementById("searchResults").style.display = "block";
    updateUsage();
  } catch (e) { showToast(e.message, "error"); }
  document.getElementById("searchLoading").style.display = "none";
  document.getElementById("searchBtn").disabled = false;
}

function renderFilters(data) {
  const tabs = [
    { key: "all", label: `All Results (${data.total})` },
    { key: "hot", label: `Hot Leads (${data.hot_leads})` },
    { key: "weak_seo", label: `Weak SEO (${data.weak_seo})` },
    { key: "no_website", label: `No Website (${data.no_website})` },
    { key: "few_reviews", label: `Few Reviews (${data.few_reviews})` },
    { key: "low_rating", label: `Low Rating (${data.low_rating})` },
    { key: "has_phone", label: `Has Phone (${data.has_phone})` },
  ];
  document.getElementById("filterTabs").innerHTML = tabs.map(t =>
    `<div class="filter-tab ${t.key === currentFilter ? 'active' : ''}" onclick="filterResults('${t.key}')">${t.label}</div>`
  ).join("");
}

function filterResults(key) {
  currentFilter = key;
  let filtered = currentResults;
  if (key === "hot") filtered = currentResults.filter(r => r.opportunity_score >= 70);
  else if (key === "weak_seo") filtered = currentResults.filter(r => r.needs.some(n => n.key === "weak_seo"));
  else if (key === "no_website") filtered = currentResults.filter(r => !r.has_website);
  else if (key === "few_reviews") filtered = currentResults.filter(r => r.needs.some(n => n.key === "few_reviews"));
  else if (key === "low_rating") filtered = currentResults.filter(r => r.needs.some(n => n.key === "low_rating"));
  else if (key === "has_phone") filtered = currentResults.filter(r => r.phone);
  renderResults(filtered);
  document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
  document.querySelector(`.filter-tab[onclick*="${key}"]`).classList.add("active");
}

function sortResults() {
  const sort = document.getElementById("sortResults").value;
  let sorted = [...currentResults];
  if (sort === "score-desc") sorted.sort((a, b) => b.opportunity_score - a.opportunity_score);
  else if (sort === "rating-asc") sorted.sort((a, b) => (a.rating || 0) - (b.rating || 0));
  else if (sort === "rating-desc") sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0));
  else if (sort === "reviews-asc") sorted.sort((a, b) => a.review_count - b.review_count);
  else if (sort === "reviews-desc") sorted.sort((a, b) => b.review_count - a.review_count);
  currentResults = sorted;
  filterResults(currentFilter);
}

function renderResults(results) {
  document.getElementById("resultsList").innerHTML = results.map(r => {
    const scoreClass = r.opportunity_score >= 70 ? "score-hot" : r.opportunity_score >= 50 ? "score-good" : r.opportunity_score >= 30 ? "score-moderate" : "score-strong";
    const badgeClass = r.opportunity_score >= 70 ? "badge-hot" : r.opportunity_score >= 50 ? "badge-good" : "badge-moderate";
    const badgeText = r.opportunity_score >= 70 ? "🔥 Hot Lead" : r.opportunity_score >= 50 ? "Good Opportunity" : "Moderate";
    return `
      <div class="lead-card">
        <div class="lead-header">
          <div>
            <span class="lead-name">${r.business_name}</span>
            <span class="lead-badge ${badgeClass}" style="margin-left:8px;">${badgeText}</span>
          </div>
          <span class="score-badge ${scoreClass}">${r.opportunity_score}</span>
        </div>
        <div class="lead-meta">
          <span>📍 ${r.city}, ${r.state}</span>
          ${r.rating ? `<span>⭐ ${r.rating} (${r.review_count})</span>` : '<span style="color:var(--text-muted);">No rating</span>'}
          ${r.phone ? `<span>📞 ${r.phone}</span>` : ''}
        </div>
        <div class="lead-needs">
          ${r.needs.map(n => `<span class="need-badge" title="${n.description}">${n.label}</span>`).join("")}
        </div>
        <div class="lead-pitch">${r.pitch_suggestion}</div>
        <div class="lead-actions">
          <button class="btn btn-sm btn-primary" onclick="saveLead(${r.id})">${r.saved ? '✓ Saved' : 'Save'}</button>
          <button class="btn btn-sm btn-secondary" onclick="generatePitch(${r.id})">AI Pitch</button>
          <button class="btn btn-sm btn-secondary" onclick="buildSiteForLead(${r.id})">Build Site</button>
          ${r.phone ? `<a class="btn btn-sm btn-ghost" href="https://wa.me/${r.phone.replace(/[^0-9]/g,'')}" target="_blank">WhatsApp</a>` : ''}
          ${r.website ? `<a class="btn btn-sm btn-ghost" href="${r.website}" target="_blank">Website</a>` : ''}
        </div>
      </div>
    `;
  }).join("");
}

async function loadPreviousSearch(id) {
  navigate("search");
  try {
    const data = await api.getSearchResults(id);
    currentResults = data.results;
    document.getElementById("resultCount").textContent = `${data.total} businesses found`;
    document.getElementById("searchNiche").value = data.niche;
    document.getElementById("searchLocation").value = data.location;
    const summary = {
      total: data.total,
      hot_leads: data.results.filter(r => r.opportunity_score >= 70).length,
      weak_seo: data.results.filter(r => (r.needs||[]).some(n => n.key === "weak_seo")).length,
      no_website: data.results.filter(r => !r.has_website).length,
      few_reviews: data.results.filter(r => (r.needs||[]).some(n => n.key === "few_reviews")).length,
      low_rating: data.results.filter(r => (r.needs||[]).some(n => n.key === "low_rating")).length,
      has_phone: data.results.filter(r => r.phone).length,
    };
    renderFilters(summary);
    renderResults(currentResults);
    document.getElementById("searchResults").style.display = "block";
  } catch (e) { showToast(e.message, "error"); }
}

// ── Save Lead ──
async function saveLead(id) {
  try {
    await api.saveLead(id);
    showToast("Lead saved to pipeline!");
    const lead = currentResults.find(r => r.id === id);
    if (lead) lead.saved = true;
    filterResults(currentFilter);
  } catch (e) { showToast(e.message, "error"); }
}

// ── AI Pitch ──
async function generatePitch(id) {
  try {
    const data = await api.generatePitch(id);
    openModal(`
      <button class="modal-close" onclick="closeModal()">✕</button>
      <h2>AI-Generated Pitch</h2>
      <div class="pitch-preview">
        <div class="pitch-subject">Subject: ${data.subject}</div>
        ${data.body.replace(/\n/g, "<br>")}
      </div>
      <div style="margin-top:16px;display:flex;gap:8px;">
        <button class="btn btn-primary" onclick="copyPitch()">Copy to Clipboard</button>
      </div>
    `);
    window._lastPitch = data;
    updateUsage();
  } catch (e) { showToast(e.message, "error"); }
}

function copyPitch() {
  if (window._lastPitch) {
    navigator.clipboard.writeText(`Subject: ${window._lastPitch.subject}\n\n${window._lastPitch.body}`);
    showToast("Pitch copied to clipboard!");
  }
}

// ── Build Site for Lead ──
function buildSiteForLead(id) {
  const r = currentResults.find(l => l.id === id);
  if (!r) return;
  navigate("websites");
  document.getElementById("webBizName").value = r.business_name;
  document.getElementById("webNiche").value = r.niche;
  document.getElementById("webLocation").value = r.city + ', ' + r.state;
  if (r.phone) document.getElementById("webPhone").value = r.phone;
}

// ── Bulk Search ──
async function doBulkSearch() {
  const niche = document.getElementById("bulkNiche").value.trim();
  const citiesRaw = document.getElementById("bulkCities").value.trim();
  if (!niche || !citiesRaw) return showToast("Enter a niche and at least one city", "error");
  const cities = citiesRaw.split(/[\n,]+/).map(c => c.trim()).filter(Boolean);
  try {
    const data = await api.bulkSearch(niche, cities);
    document.getElementById("bulkResults").innerHTML = `
      <div class="card"><h3>${data.total} businesses found across ${data.cities.length} cities</h3></div>
      ${data.results.slice(0, 30).map(r => `
        <div class="lead-card" style="margin-top:8px;">
          <div class="lead-header">
            <span class="lead-name">${r.business_name}</span>
            <span class="score-badge ${r.opportunity_score >= 70 ? 'score-hot' : r.opportunity_score >= 50 ? 'score-good' : 'score-moderate'}">${r.opportunity_score}</span>
          </div>
          <div class="lead-meta"><span>📍 ${r.city}, ${r.state}</span>${r.rating ? `<span>⭐ ${r.rating}</span>` : ''}<span>📞 ${r.phone}</span></div>
        </div>
      `).join("")}
    `;
    updateUsage();
  } catch (e) { showToast(e.message, "error"); }
}

// ── Niche Scanner ──
async function doNicheScan() {
  const niches = document.getElementById("nicheScanNiches").value.split(",").map(s => s.trim()).filter(Boolean);
  const cities = document.getElementById("nicheScanCities").value.split(",").map(s => s.trim()).filter(Boolean);
  if (!niches.length || !cities.length) return showToast("Enter at least one niche and one city", "error");
  try {
    const data = await api.nicheScan(niches, cities, document.getElementById("nicheScanService").value);
    document.getElementById("nicheScanResults").innerHTML = `
      <table class="data-table">
        <thead><tr><th>Niche</th><th>City</th><th>Businesses</th><th>Weak %</th><th>Opportunity</th><th>Avg CPC</th><th>Monthly Volume</th><th>Action</th></tr></thead>
        <tbody>${data.results.map(r => `
          <tr>
            <td>${r.niche}</td><td>${r.city}</td><td>${r.business_count}</td>
            <td>${r.weak_presence_pct}%</td>
            <td><span class="score-badge ${r.opportunity_score >= 70 ? 'score-hot' : r.opportunity_score >= 50 ? 'score-good' : 'score-moderate'}">${r.opportunity_score}</span></td>
            <td>$${r.avg_cpc}</td><td>${r.monthly_search_volume.toLocaleString()}</td>
            <td><button class="btn btn-sm btn-primary" onclick="searchFromNicheScan(this)" data-niche="${r.niche.replace(/"/g,'&quot;')}" data-city="${r.city.replace(/"/g,'&quot;')}">Search Leads</button></td>
          </tr>
        `).join("")}</tbody>
      </table>
    `;
  } catch (e) { showToast(e.message, "error"); }
}

function searchFromNicheScan(btn) {
  document.getElementById('searchNiche').value = btn.dataset.niche;
  document.getElementById('searchLocation').value = btn.dataset.city;
  navigate('search');
}

// ── SERP Analyzer ──
async function doSerpAnalysis() {
  const query = document.getElementById("serpQuery").value.trim();
  if (!query) return showToast("Enter a keyword or URL", "error");
  try {
    const data = await api.serpAnalyze(query);
    if (data.mode === "keyword") {
      document.getElementById("serpResults").innerHTML = `
        <div class="stats-grid" style="margin-bottom:20px;">
          <div class="card"><div class="card-title">Keyword Difficulty</div><div class="card-value">${data.keyword_difficulty}/100</div></div>
          <div class="card"><div class="card-title">Monthly Volume</div><div class="card-value">${data.monthly_volume.toLocaleString()}</div></div>
          <div class="card"><div class="card-title">CPC</div><div class="card-value">$${data.cpc}</div></div>
        </div>
        <h3 style="margin-bottom:12px;">Top 10 Results for "${data.query}"</h3>
        ${data.competitors.map(c => `
          <div class="serp-item">
            <span class="serp-position">${c.position}</span>
            <div style="display:inline-block;vertical-align:top;">
              <div class="serp-url">${c.url}</div>
              <div class="serp-title">${c.title}</div>
              <div class="serp-meta">
                <span>DA: ${c.domain_authority}</span>
                <span>Words: ${c.word_count.toLocaleString()}</span>
                <span>Difficulty: <span class="score-badge ${c.difficulty >= 60 ? 'score-hot' : c.difficulty >= 40 ? 'score-good' : 'score-strong'}">${c.difficulty}</span></span>
                <span>${c.has_ssl ? '🔒 SSL' : '⚠️ No SSL'}</span>
                <span>${c.has_schema ? '✓ Schema' : '✗ No Schema'}</span>
              </div>
            </div>
          </div>
        `).join("")}
      `;
    } else {
      document.getElementById("serpResults").innerHTML = `
        <div class="stats-grid" style="margin-bottom:20px;">
          <div class="card"><div class="card-title">Domain Authority</div><div class="card-value">${data.domain_authority}</div></div>
          <div class="card"><div class="card-title">PageSpeed (Mobile)</div><div class="card-value">${data.page_speed_mobile}/100</div></div>
          <div class="card"><div class="card-title">Backlinks</div><div class="card-value">${data.backlinks.toLocaleString()}</div></div>
          <div class="card"><div class="card-title">Organic Traffic</div><div class="card-value">${data.organic_traffic.toLocaleString()}/mo</div></div>
        </div>
        <h3 style="margin-bottom:12px;">Issues Found</h3>
        ${data.issues.map(i => `
          <div class="card" style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div>
                <span class="need-badge" style="${i.severity === 'high' ? '' : i.severity === 'medium' ? 'background:rgba(249,115,22,0.1);color:var(--orange);border-color:rgba(249,115,22,0.2);' : 'background:rgba(234,179,8,0.1);color:var(--yellow);border-color:rgba(234,179,8,0.2);'}">${i.severity.toUpperCase()}</span>
                <span style="margin-left:8px;">${i.title}</span>
              </div>
            </div>
            <p style="font-size:0.8rem;color:var(--text-secondary);margin-top:6px;">Fix: ${i.fix}</p>
          </div>
        `).join("")}
      `;
    }
  } catch (e) { showToast(e.message, "error"); }
}

// ── NAP Audit ──
async function doNapAudit() {
  const name = document.getElementById("napName").value.trim();
  if (!name) return showToast("Enter a business name", "error");
  try {
    const data = await api.napAudit(name, document.getElementById("napAddress").value, document.getElementById("napPhone").value);
    document.getElementById("napResults").innerHTML = `
      <div class="stats-grid" style="margin-bottom:20px;">
        <div class="card"><div class="card-title">NAP Score</div><div class="card-value" style="color:${data.score >= 70 ? 'var(--green)' : data.score >= 40 ? 'var(--orange)' : 'var(--red)'};">${data.score}%</div></div>
        <div class="card"><div class="card-title">Correct Listings</div><div class="card-value" style="color:var(--green);">${data.correct}</div></div>
        <div class="card"><div class="card-title">Incorrect</div><div class="card-value" style="color:var(--orange);">${data.incorrect}</div></div>
        <div class="card"><div class="card-title">Missing</div><div class="card-value" style="color:var(--red);">${data.missing}</div></div>
      </div>
      <table class="data-table">
        <thead><tr><th>Directory</th><th>Status</th><th>Name</th><th>Address</th><th>Phone</th></tr></thead>
        <tbody>${data.results.map(r => `
          <tr>
            <td>${r.directory}</td>
            <td><span class="nap-status ${r.status === 'found_correct' ? 'nap-correct' : r.status === 'found_incorrect' ? 'nap-incorrect' : 'nap-missing'}">${r.status === 'found_correct' ? 'Correct' : r.status === 'found_incorrect' ? 'Incorrect' : 'Missing'}</span></td>
            <td>${r.name_match ? '✓' : '✗'}</td>
            <td>${r.address_match ? '✓' : '✗'}</td>
            <td>${r.phone_match ? '✓' : '✗'}</td>
          </tr>
        `).join("")}</tbody>
      </table>
    `;
  } catch (e) { showToast(e.message, "error"); }
}

// ── Backlinks ──
async function doBacklinks() {
  const domain = document.getElementById("backlinkDomain").value.trim();
  if (!domain) return showToast("Enter a domain", "error");
  try {
    const data = await api.backlinks(domain);
    document.getElementById("backlinkResults").innerHTML = `
      <div class="stats-grid" style="margin-bottom:20px;">
        <div class="card"><div class="card-title">Total Backlinks</div><div class="card-value">${data.total_backlinks}</div></div>
        <div class="card"><div class="card-title">Referring Domains</div><div class="card-value">${data.referring_domains}</div></div>
        <div class="card"><div class="card-title">Dofollow %</div><div class="card-value">${data.dofollow_pct}%</div></div>
      </div>
      <table class="data-table">
        <thead><tr><th>Source</th><th>DR</th><th>Anchor</th><th>Type</th><th>Geo Fit</th><th>First Seen</th></tr></thead>
        <tbody>${data.backlinks.map(b => `
          <tr>
            <td><a href="${b.source_url}" target="_blank" style="font-size:0.8rem;">${b.source_domain}</a></td>
            <td>${b.domain_rating}</td>
            <td>${b.anchor_text}</td>
            <td><span style="color:${b.link_type === 'dofollow' ? 'var(--green)' : 'var(--text-muted)'}">${b.link_type}</span></td>
            <td><span style="color:${b.geo_fit === 'high' ? 'var(--green)' : b.geo_fit === 'medium' ? 'var(--orange)' : 'var(--text-muted)'}">${b.geo_fit}</span></td>
            <td>${b.first_seen}</td>
          </tr>
        `).join("")}</tbody>
      </table>
    `;
  } catch (e) { showToast(e.message, "error"); }
}

// ── Rank Tracking ──
async function doRankTracking() {
  const domain = document.getElementById("rankDomain").value.trim();
  const keywords = document.getElementById("rankKeywords").value.split(",").map(s => s.trim()).filter(Boolean);
  if (!domain || !keywords.length) return showToast("Enter a domain and keywords", "error");
  try {
    const data = await api.rankTracking(domain, keywords);
    document.getElementById("rankResults").innerHTML = `
      <table class="data-table">
        <thead><tr><th>Keyword</th><th>Current Rank</th><th>Previous</th><th>Best</th><th>Trend (14d)</th><th>Volume</th></tr></thead>
        <tbody>${data.keywords.map(k => {
          const change = k.previous_rank - k.current_rank;
          const changeColor = change > 0 ? 'var(--green)' : change < 0 ? 'var(--red)' : 'var(--text-muted)';
          const sparkline = k.history.map((v,i) => {
            const max = Math.max(...k.history); const min = Math.min(...k.history);
            const h = 20; const y = h - ((v - min) / (max - min + 1)) * h;
            return `${i * 5},${y}`;
          }).join(" ");
          return `<tr>
            <td>${k.keyword}</td>
            <td><strong>#${k.current_rank}</strong></td>
            <td style="color:${changeColor}">${change > 0 ? '↑' : change < 0 ? '↓' : '→'} #${k.previous_rank} (${change > 0 ? '+' : ''}${change})</td>
            <td>#${k.best_rank}</td>
            <td><svg width="70" height="24" viewBox="0 0 70 24"><polyline points="${sparkline}" fill="none" stroke="var(--green)" stroke-width="1.5"/></svg></td>
            <td>${k.search_volume.toLocaleString()}</td>
          </tr>`;
        }).join("")}</tbody>
      </table>
    `;
  } catch (e) { showToast(e.message, "error"); }
}

// ── Link Health ──
async function doLinkHealth() {
  const domain = document.getElementById("linkHealthDomain").value.trim();
  if (!domain) return showToast("Enter a domain", "error");
  try {
    const data = await api.linkHealth(domain);
    const anchors = Object.entries(data.anchor_distribution).sort((a,b) => b[1]-a[1]);
    const maxAnchor = Math.max(...anchors.map(a => a[1]));
    document.getElementById("linkHealthResults").innerHTML = `
      <div class="stats-grid" style="margin-bottom:20px;">
        <div class="card"><div class="card-title">Total Backlinks</div><div class="card-value">${data.total_backlinks}</div></div>
        <div class="card"><div class="card-title">Toxic Score</div><div class="card-value" style="color:${data.toxic_score > 20 ? 'var(--red)' : 'var(--green)'};">${data.toxic_score}%</div></div>
        <div class="card"><div class="card-title">Velocity Alert</div><div class="card-value">${data.velocity_alert ? '⚠️ Yes' : '✓ Normal'}</div></div>
      </div>
      <h3 style="margin-bottom:12px;">Anchor Text Distribution</h3>
      ${anchors.map(([text, count]) => `
        <div style="margin-bottom:8px;"><div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:4px;"><span>${text}</span><span>${count}</span></div><div class="progress-bar"><div class="progress-fill" style="width:${count/maxAnchor*100}%"></div></div></div>
      `).join("")}
    `;
  } catch (e) { showToast(e.message, "error"); }
}

// ── Pipeline ──
async function loadPipeline() {
  try {
    const data = await api.getPipeline();
    if (data.total === 0) {
      document.getElementById("pipelineContent").innerHTML = `<div class="empty-state"><h3>No saved leads yet</h3><p>Search for leads and save them to see them here.</p><button class="btn btn-primary" onclick="navigate('search')">Search Leads</button></div>`;
      return;
    }
    const stageNames = { new: "New", contacted: "Contacted", replied: "Replied", proposal: "Proposal", closed: "Closed" };
    document.getElementById("pipelineContent").innerHTML = `
      <div class="kanban">
        ${Object.entries(data.stages).map(([stage, leads]) => `
          <div class="kanban-col">
            <div class="kanban-col-title"><span>${stageNames[stage]}</span><span>${leads.length}</span></div>
            ${leads.map(l => `
              <div class="kanban-card">
                <h4>${l.business_name}</h4>
                <p>${l.city}, ${l.state} · ${l.niche}</p>
                <div style="margin-top:6px;display:flex;gap:4px;">
                  ${Object.keys(stageNames).filter(s => s !== stage).map(s => `<button class="btn btn-sm btn-ghost" onclick="moveStage(${l.id},'${s}')" style="font-size:0.7rem;">${stageNames[s]}</button>`).join("")}
                </div>
              </div>
            `).join("")}
          </div>
        `).join("")}
      </div>
    `;
  } catch (e) { showToast(e.message, "error"); }
}

async function moveStage(id, stage) {
  try { await api.updateStage(id, stage); loadPipeline(); } catch (e) { showToast(e.message, "error"); }
}

// ── Competitor Compare ──
async function doCompare() {
  const url1 = document.getElementById("compareUrl1").value.trim();
  const url2 = document.getElementById("compareUrl2").value.trim();
  if (!url1 || !url2) return showToast("Enter both URLs", "error");
  try {
    const data = await api.competitorCompare(url1, url2);
    const metrics = ["domain_authority","page_speed","backlinks","organic_keywords","monthly_traffic","review_count","avg_rating"];
    const labels = {domain_authority:"Domain Authority",page_speed:"Page Speed",backlinks:"Backlinks",organic_keywords:"Organic Keywords",monthly_traffic:"Monthly Traffic",review_count:"Reviews",avg_rating:"Avg Rating"};
    document.getElementById("compareResults").innerHTML = `
      <div class="compare-grid">
        <div class="compare-col">
          <h3 style="margin-bottom:16px;word-break:break-all;">${data.site1.url}</h3>
          ${metrics.map(m => {
            const better = data.site1[m] >= data.site2[m];
            return `<div class="metric-row"><span class="metric-label">${labels[m]}</span><span class="metric-value ${better ? 'good' : 'bad'}">${typeof data.site1[m] === 'number' ? data.site1[m].toLocaleString() : data.site1[m]}</span></div>`;
          }).join("")}
        </div>
        <div class="compare-vs">VS</div>
        <div class="compare-col">
          <h3 style="margin-bottom:16px;word-break:break-all;">${data.site2.url}</h3>
          ${metrics.map(m => {
            const better = data.site2[m] >= data.site1[m];
            return `<div class="metric-row"><span class="metric-label">${labels[m]}</span><span class="metric-value ${better ? 'good' : 'bad'}">${typeof data.site2[m] === 'number' ? data.site2[m].toLocaleString() : data.site2[m]}</span></div>`;
          }).join("")}
        </div>
      </div>
    `;
  } catch (e) { showToast(e.message, "error"); }
}

// ── Proposals ──
async function doCreateProposal() {
  const title = document.getElementById("proposalTitle").value.trim();
  const client = document.getElementById("proposalClient").value.trim();
  if (!title || !client) return showToast("Enter title and client name", "error");
  try {
    const data = await api.createProposal(title, client);
    openModal(`<button class="modal-close" onclick="closeModal()">✕</button><h2>${title}</h2><div style="white-space:pre-wrap;font-size:0.85rem;color:var(--text-secondary);line-height:1.7;">${data.content}</div>`);
    loadProposals();
  } catch (e) { showToast(e.message, "error"); }
}
async function loadProposals() {
  try {
    const data = await api.getProposals();
    document.getElementById("proposalsList").innerHTML = data.length ? data.map(p => `<div class="card" style="margin-bottom:8px;"><div style="display:flex;justify-content:space-between;"><strong>${p.title}</strong><span class="lead-badge badge-moderate">${p.status}</span></div><p style="font-size:0.8rem;color:var(--text-secondary);">${p.client_name} · ${timeAgo(p.created_at)}</p></div>`).join("") : '<div class="empty-state"><h3>No proposals yet</h3><p>Create your first proposal above.</p></div>';
  } catch (e) {}
}

// ── Campaigns ──
async function doCreateCampaign() {
  const name = document.getElementById("campaignName").value.trim();
  if (!name) return showToast("Enter a campaign name", "error");
  try { await api.createCampaign(name); showToast("Campaign created!"); loadCampaigns(); document.getElementById("campaignName").value = ""; } catch (e) { showToast(e.message, "error"); }
}
async function loadCampaigns() {
  try {
    const data = await api.getCampaigns();
    document.getElementById("campaignsList").innerHTML = data.length ? data.map(c => `<div class="card" style="margin-bottom:8px;"><div style="display:flex;justify-content:space-between;"><strong>${c.name}</strong><span class="lead-badge badge-moderate">${c.status}</span></div><p style="font-size:0.8rem;color:var(--text-secondary);">Leads: ${c.total_leads} · Sent: ${c.emails_sent} · Replies: ${c.replies} · ${timeAgo(c.created_at)}</p></div>`).join("") : '<div class="empty-state"><h3>No campaigns yet</h3><p>Create your first campaign to start outreach at scale.</p></div>';
  } catch (e) {}
}

// ── Templates ──
async function doCreateTemplate() {
  const name = document.getElementById("tplName").value.trim();
  const subject = document.getElementById("tplSubject").value.trim();
  const body = document.getElementById("tplBody").value.trim();
  if (!name || !subject || !body) return showToast("Fill in all fields", "error");
  try { await api.createTemplate(name, subject, body); showToast("Template saved!"); loadTemplates(); } catch (e) { showToast(e.message, "error"); }
}
async function loadTemplates() {
  try {
    const data = await api.getTemplates();
    document.getElementById("templatesList").innerHTML = data.length ? data.map(t => `<div class="card" style="margin-bottom:8px;"><strong>${t.name}</strong><p style="font-size:0.8rem;color:var(--text-secondary);margin-top:4px;">Subject: ${t.subject}</p><p style="font-size:0.8rem;color:var(--text-muted);margin-top:4px;white-space:pre-wrap;">${t.body}</p></div>`).join("") : '<div class="empty-state"><h3>No templates yet</h3><p>Create reusable email templates above.</p></div>';
  } catch (e) {}
}

// ── Case Studies ──
async function doCreateCaseStudy() {
  const title = document.getElementById("csTitle").value.trim();
  const client = document.getElementById("csClient").value.trim();
  const desc = document.getElementById("csDescription").value.trim();
  if (!title || !client) return showToast("Fill in title and client", "error");
  try { await api.createCaseStudy(title, client, desc); showToast("Case study created!"); loadCaseStudies(); } catch (e) { showToast(e.message, "error"); }
}
async function loadCaseStudies() {
  try {
    const data = await api.getCaseStudies();
    document.getElementById("caseStudiesList").innerHTML = data.length ? data.map(s => `<div class="card" style="margin-bottom:8px;"><strong>${s.title}</strong><p style="font-size:0.8rem;color:var(--text-secondary);">${s.client_name} · ${s.published ? 'Published' : 'Draft'} · ${timeAgo(s.created_at)}</p></div>`).join("") : '<div class="empty-state"><h3>No case studies yet</h3><p>Create your first case study above.</p></div>';
  } catch (e) {}
}

// ── ROI Calculator ──
async function doRoiCalc() {
  try {
    const data = await api.roiCalculate(
      parseFloat(document.getElementById("roiRevenue").value),
      parseInt(document.getElementById("roiTraffic").value),
      parseFloat(document.getElementById("roiIncrease").value),
      parseFloat(document.getElementById("roiConversion").value),
    );
    document.getElementById("roiResults").innerHTML = `
      <div class="stats-grid">
        <div class="card"><div class="card-title">Additional Traffic/mo</div><div class="card-value" style="color:var(--green);">+${data.additional_traffic.toLocaleString()}</div></div>
        <div class="card"><div class="card-title">New Leads/mo</div><div class="card-value" style="color:var(--green);">+${data.additional_leads_per_month}</div></div>
        <div class="card"><div class="card-title">Additional Revenue/mo</div><div class="card-value" style="color:var(--green);">$${data.additional_monthly_revenue.toLocaleString()}</div></div>
        <div class="card"><div class="card-title">Additional Revenue/yr</div><div class="card-value" style="color:var(--green);">$${data.additional_annual_revenue.toLocaleString()}</div></div>
      </div>
      <div class="card" style="margin-top:16px;text-align:center;">
        <p style="font-size:1.2rem;font-weight:600;">For every $1 you invest in SEO, your client gets <span style="color:var(--green);">$${Math.round(data.additional_monthly_revenue / 500)}</span> back</p>
        <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:8px;">Based on avg. customer value of $${data.avg_customer_value.toLocaleString()}</p>
      </div>
    `;
  } catch (e) { showToast(e.message, "error"); }
}

// ── Website Generator ──
async function doGenerateWebsite() {
  const name = document.getElementById("webBizName").value.trim();
  const niche = document.getElementById("webNiche").value.trim();
  const location = document.getElementById("webLocation").value.trim();
  if (!name || !niche || !location) return showToast("Fill in business name, niche, and location", "error");
  try {
    const phone = document.getElementById("webPhone").value.trim() || "(555) 123-4567";
    const data = await api.generateWebsite(name, niche, location, phone);
    document.getElementById("websitePreview").innerHTML = `
      <div class="website-preview">
        <div class="hero-section">
          <h1>${name}</h1>
          <p>Professional ${niche} Services in ${location}</p>
          <p style="margin-top:16px;"><strong>Call Now: ${phone}</strong></p>
        </div>
        <div class="services-section">
          <h2>Our Services</h2>
          <div class="services-grid">
            <div class="service-card"><h3>Service 1</h3><p>Professional ${niche.toLowerCase()} service with guaranteed satisfaction</p></div>
            <div class="service-card"><h3>Service 2</h3><p>Emergency ${niche.toLowerCase()} available 24/7</p></div>
            <div class="service-card"><h3>Service 3</h3><p>Free estimates and competitive pricing</p></div>
          </div>
        </div>
        <div class="contact-section">
          <h2>Contact Us</h2>
          <p>${name} · ${location}</p>
          <p>📞 ${phone}</p>
          <p style="margin-top:12px;"><strong>Serving ${location} and surrounding areas</strong></p>
        </div>
      </div>
      <p style="text-align:center;margin-top:12px;color:var(--text-muted);font-size:0.85rem;">Demo website generated. In production, this would be a fully hosted site.</p>
    `;
    showToast("Website generated!");
  } catch (e) { showToast(e.message, "error"); }
}

// ── Settings ──
function loadSettings() {
  if (api.user) {
    document.getElementById("settingsName").value = api.user.full_name;
    document.getElementById("settingsEmail").value = api.user.email;
  }
}

// ── Helpers ──
function openModal(html) {
  document.getElementById("modalContent").innerHTML = html;
  document.getElementById("modalOverlay").style.display = "flex";
}
function closeModal(e) {
  if (!e || e.target === document.getElementById("modalOverlay"))
    document.getElementById("modalOverlay").style.display = "none";
}
function showToast(msg, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ""; }
function getInitials(name) { return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2); }
function timeAgo(dateStr) {
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}
async function updateUsage() {
  try {
    const data = await api.getDashboard();
    document.getElementById("usageText").textContent = `${data.searches_used} / ${data.searches_limit} searches`;
  } catch (e) {}
}

// ── Start ──
init();
