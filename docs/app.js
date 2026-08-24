// Edge Computing PhD Intelligence Dashboard Client Logic

let dashboardData = {
  meta: {},
  trends: [],
  supervisors: [],
  items: []
};

let activeType = "all";
let minScore = 7.5;
let searchQuery = "";

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  fetchData();
  setupEventListeners();
});

function initTheme() {
  const savedTheme = localStorage.getItem("theme") || "light";
  if (savedTheme === "dark") {
    document.body.classList.replace("light-mode", "dark-mode");
  }
}

function toggleTheme() {
  if (document.body.classList.contains("light-mode")) {
    document.body.classList.replace("light-mode", "dark-mode");
    localStorage.setItem("theme", "dark");
  } else {
    document.body.classList.replace("dark-mode", "light-mode");
    localStorage.setItem("theme", "light");
  }
}

async function fetchData() {
  try {
    const res = await fetch("data.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    dashboardData = await res.json();
    renderAll();
  } catch (err) {
    console.warn("Could not load data.json, using fallback sample data:", err);
    // Load sample fallback for initial preview
    loadSampleData();
  }
}

function loadSampleData() {
  dashboardData = {
    meta: {
      last_updated: new Date().toISOString().split("T")[0],
      total_items: 42,
      high_relevance_count: 17,
      papers_count: 24,
      conferences_count: 8,
      opportunities_count: 5
    },
    trends: [
      { topic: "Edge AI", direction: "↑↑", status: "Surging", recent_count: 12 },
      { topic: "Federated Learning", direction: "↑", status: "Rising", recent_count: 8 },
      { topic: "6G + Edge", direction: "↑↑", status: "Surging", recent_count: 7 },
      { topic: "Computation Offloading", direction: "↑", status: "Rising", recent_count: 6 },
      { topic: "Edge Security", direction: "→", status: "Stable", recent_count: 4 }
    ],
    supervisors: [
      { name: "Mahadev Satyanarayanan", institution: "Carnegie Mellon University", publication_count: 6, average_relevance: 9.4, topics: ["Cloudlets", "Edge Computing"] },
      { name: "Mung Chiang", institution: "Purdue / Princeton", publication_count: 4, average_relevance: 9.0, topics: ["Fog Networking", "Resource Allocation"] },
      { name: "Ion Stoica", institution: "UC Berkeley", publication_count: 3, average_relevance: 8.8, topics: ["Sky Computing", "Distributed AI"] }
    ],
    items: [
      {
        id: "sample_1",
        title: "Adaptive Computation Offloading for Edge AI in 6G Networks",
        url: "https://arxiv.org/abs/2608.1001",
        source: "IEEE Transactions on Mobile Computing",
        item_type: "paper",
        authors: ["J. Zhang", "L. Wang", "X. Chen"],
        publication_date: new Date().toISOString().split("T")[0],
        abstract: "We formulate an energy-efficient Lyapunov optimization framework for real-time edge AI model inference offloading under stochastic wireless channel variations in 6G MEC.",
        venue: "IEEE TMC",
        score: {
          final_score: 9.6,
          reasons: ["Primary topic match: Edge AI", "Tier 1 IEEE source", "Aligned with learning stage"]
        },
        intelligence: {
          why_it_matters: "Addresses key latency-energy bottlenecks for real-time AI offloading in 6G edge environments.",
          research_problem: "Minimizing inference latency while avoiding edge node battery depletion.",
          methodology: "Lyapunov optimization with online queue stability control.",
          key_contribution: "Reduces tail latency by 34% compared to baseline heuristic schedulers.",
          potential_gap: "Potential research direction: Evaluate under heterogeneous edge device clusters with intermittent connectivity."
        }
      },
      {
        id: "sample_2",
        title: "Fully Funded PhD Studentship in Distributed Edge Intelligence & Federated Learning",
        url: "https://www.jobs.ac.uk/job/phd-edge-ai",
        source: "University Research Group",
        item_type: "phd_opportunity",
        authors: ["Prof. S. Dustdar"],
        publication_date: new Date().toISOString().split("T")[0],
        abstract: "3.5-year fully funded PhD position covering international tuition and living stipend to research communication-efficient federated learning across edge-cloud continuum.",
        venue: "TU Wien Distributed Systems Group",
        institution: "TU Wien",
        score: {
          final_score: 9.2,
          reasons: ["PhD Opportunity in core topic", "Tier 2 University Lab", "Full Funding"]
        }
      }
    ]
  };
  renderAll();
}

function setupEventListeners() {
  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);

  // Search input
  const searchInput = document.getElementById("search-input");
  searchInput.addEventListener("input", (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    renderItems();
  });

  // Type pills
  const typePills = document.querySelectorAll("#type-filters .pill");
  typePills.forEach(pill => {
    pill.addEventListener("click", () => {
      typePills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeType = pill.getAttribute("data-type");
      renderItems();
    });
  });

  // Score selector
  const scoreSelect = document.getElementById("min-score-select");
  scoreSelect.addEventListener("change", (e) => {
    minScore = parseFloat(e.target.value);
    renderItems();
  });
}

function renderAll() {
  renderMeta();
  renderTrends();
  renderSupervisors();
  renderItems();
}

function renderMeta() {
  const meta = dashboardData.meta || {};
  document.getElementById("last-updated").textContent = `Updated: ${meta.last_updated || "Today"}`;
  document.getElementById("metric-total").textContent = meta.total_items || dashboardData.items.length;
  document.getElementById("metric-high-relevance").textContent = meta.high_relevance_count || 0;
  document.getElementById("metric-papers").textContent = meta.papers_count || 0;
  document.getElementById("metric-confs").textContent = meta.conferences_count || 0;
  document.getElementById("metric-opps").textContent = meta.opportunities_count || 0;
}

function renderTrends() {
  const container = document.getElementById("trends-list");
  container.innerHTML = "";
  const trends = dashboardData.trends || [];

  if (trends.length === 0) {
    container.innerHTML = `<div style="font-size: 12px; color: var(--text-muted);">No trend data yet.</div>`;
    return;
  }

  trends.forEach(t => {
    let pillClass = "trend-steady";
    if (t.direction === "↑↑") pillClass = "trend-up";
    else if (t.direction === "↑") pillClass = "trend-rising";
    else if (t.direction === "↓") pillClass = "trend-down";

    const div = document.createElement("div");
    div.className = "trend-item";
    div.innerHTML = `
      <span><strong>${t.topic}</strong> <span style="font-size: 11px; color: var(--text-muted);">(${t.recent_count})</span></span>
      <span class="trend-pill ${pillClass}">${t.direction} ${t.status}</span>
    `;
    container.appendChild(div);
  });
}

function renderSupervisors() {
  const container = document.getElementById("supervisors-list");
  container.innerHTML = "";
  const sups = dashboardData.supervisors || [];

  if (sups.length === 0) {
    container.innerHTML = `<div style="font-size: 12px; color: var(--text-muted);">No supervisor data yet.</div>`;
    return;
  }

  sups.forEach(s => {
    const div = document.createElement("div");
    div.className = "supervisor-item";
    div.innerHTML = `
      <div class="supervisor-name">${s.name}</div>
      <div class="supervisor-meta">${s.institution || "Academic Lab"} &bull; ${s.publication_count} papers (Avg: ${s.average_relevance}/10)</div>
    `;
    container.appendChild(div);
  });
}

function renderItems() {
  const container = document.getElementById("items-container");
  container.innerHTML = "";

  const items = dashboardData.items || [];
  const filtered = items.filter(item => {
    // Score filter
    const score = item.score ? item.score.final_score : 0;
    if (score < minScore) return false;

    // Type filter
    if (activeType !== "all" && item.item_type !== activeType) {
      if (activeType === "paper" && !["paper", "preprint", "survey"].includes(item.item_type)) {
        return false;
      } else if (activeType !== "paper") {
        return false;
      }
    }

    // Search query
    if (searchQuery) {
      const title = (item.title || "").toLowerCase();
      const abstract = (item.abstract || "").toLowerCase();
      const authors = (item.authors || []).join(" ").toLowerCase();
      const venue = (item.venue || "").toLowerCase();
      if (!title.includes(searchQuery) && !abstract.includes(searchQuery) && !authors.includes(searchQuery) && !venue.includes(searchQuery)) {
        return false;
      }
    }

    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="padding: 40px; text-align: center; color: var(--text-muted); background: var(--bg-card); border-radius: var(--radius-md);">
        <h3>No matching research items found</h3>
        <p style="font-size: 13px; margin-top: 6px;">Try adjusting the search query, topic filter, or minimum score threshold.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(item => {
    const score = item.score ? item.score.final_score : 7.0;
    let scoreClass = "score-good";
    if (score >= 9.0) scoreClass = "score-crit";
    else if (score >= 8.0) scoreClass = "score-high";
    else if (score < 6.5) scoreClass = "score-mod";

    const card = document.createElement("article");
    card.className = `item-card ${item.item_type || "paper"}`;

    let intelHtml = "";
    if (item.intelligence) {
      intelHtml = `
        <div class="item-intel-box">
          <div class="intel-row"><span class="intel-lbl">Why it matters:</span> ${item.intelligence.why_it_matters}</div>
          ${item.intelligence.research_problem && item.intelligence.research_problem !== "Not determinable from available metadata." ? `<div class="intel-row"><span class="intel-lbl">Research Problem:</span> ${item.intelligence.research_problem}</div>` : ""}
          ${item.intelligence.methodology && item.intelligence.methodology !== "Not determinable from available metadata." ? `<div class="intel-row"><span class="intel-lbl">Methodology:</span> ${item.intelligence.methodology}</div>` : ""}
          <div class="intel-row"><span class="intel-lbl">Potential Gap:</span> <em>${item.intelligence.potential_gap}</em></div>
        </div>
      `;
    }

    let reasonsHtml = "";
    if (item.score && item.score.reasons) {
      reasonsHtml = `
        <div class="reasons-tag-box">
          ${item.score.reasons.map(r => `<span class="reason-pill">${r}</span>`).join("")}
        </div>
      `;
    }

    card.innerHTML = `
      <div class="item-header">
        <a href="${item.url}" class="card-title" target="_blank" rel="noopener noreferrer">${item.title}</a>
        <span class="card-score ${scoreClass}">${score}/10</span>
      </div>
      <div class="item-meta">
        <strong>${item.venue || item.source}</strong> &bull; ${item.publication_date || "Recent"}
        ${item.authors && item.authors.length ? ` &bull; ${item.authors.slice(0, 3).join(", ")}` : ""}
        ${item.deadline ? ` &bull; <strong style="color: var(--accent-red)">Deadline: ${item.deadline}</strong>` : ""}
      </div>
      <div class="item-abstract">${item.abstract ? item.abstract.substring(0, 320) + (item.abstract.length > 320 ? "..." : "") : "No abstract available."}</div>
      ${intelHtml}
      ${reasonsHtml}
    `;
    container.appendChild(card);
  });
}
