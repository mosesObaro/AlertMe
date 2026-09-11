// Edge Computing PhD Intelligence Dashboard Client Logic

let dashboardData = {
  meta: {},
  trends: [],
  supervisors: [],
  researchers: [],
  opportunities: [],
  scholarships: [],
  target_countries: {},
  items: []
};

let activeType = "all";
let minScore = 7.5;
let searchQuery = "";

// Opportunity filters
let oppCountryFilter = "all";
let oppRecruitmentFilter = "all";
let oppFundingFilter = "all";
let oppDependantFilter = "all";

// Researcher filters
let researcherSearch = "";
let researcherRecruitingFilter = "all";

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
    loadSampleData();
  }
}

function loadSampleData() {
  dashboardData = {
    meta: {
      last_updated: new Date().toISOString().split("T")[0],
      total_items: 42,
      high_relevance_count: 17,
      active_recruitment_count: 8,
      opportunities_count: 6,
      scholarships_count: 7
    },
    trends: [
      { topic: "Edge AI & Intelligence", direction: "↑↑", status: "Surging", recent_count: 14 },
      { topic: "Federated Learning at Edge", direction: "↑", status: "Rising", recent_count: 9 },
      { topic: "Distributed Systems & MEC", direction: "↑↑", status: "Surging", recent_count: 8 },
      { topic: "Adaptive Offloading", direction: "↑", status: "Rising", recent_count: 6 },
      { topic: "Edge-Cloud Continuum", direction: "→", status: "Stable", recent_count: 5 }
    ],
    supervisors: [
      { name: "Prof. Dr. Schahram Dustdar", institution: "TU Wien", country: "Germany", publication_count: 12, average_relevance: 9.4, recruitment_status: "actively_recruiting", recruitment_quote: "Looking for excellent PhD candidates in Edge Intelligence and Distributed Systems.", topics: ["Edge Intelligence", "Distributed Systems", "IoT"], scholar_url: "https://scholar.google.com/citations?user=dustdar" },
      { name: "Prof. Mahadev Satyanarayanan", institution: "Carnegie Mellon University", country: "United States", publication_count: 10, average_relevance: 9.5, recruitment_status: "likely_recruiting", topics: ["Edge Computing", "Cloudlets", "Wearable Cognitive Assistance"], scholar_url: "https://scholar.google.com/citations?user=satya" },
      { name: "Prof. Jiannong Cao", institution: "Hong Kong Polytechnic University", country: "Hong Kong", publication_count: 9, average_relevance: 9.1, recruitment_status: "actively_recruiting", recruitment_quote: "Postdoc and PhD student positions available in Edge AI and Wireless Distributed Systems.", topics: ["Edge Computing", "Distributed AI", "Wireless Networks"], scholar_url: "https://scholar.google.com/citations?user=jcao" }
    ],
    researchers: [
      {
        name: "Prof. Dr. Schahram Dustdar",
        institution: "TU Wien",
        country: "Germany",
        publication_count: 12,
        composite_score: 9.4,
        recruitment_status: "actively_recruiting",
        recruitment_quote: "Looking for excellent PhD candidates in Edge Intelligence and Distributed Systems.",
        research_topics: ["Edge Intelligence", "Distributed Systems", "IoT", "Federated Learning"],
        scholar_url: "https://scholar.google.com/citations?user=dustdar",
        lab_page: "https://dsg.tuwien.ac.at",
        recent_papers: [
          { title: "Continuous Learning at the Edge: Foundations and Challenges", venue: "IEEE Internet Computing", score: 9.5, date: "2026-08-15" }
        ]
      },
      {
        name: "Prof. Jiannong Cao",
        institution: "Hong Kong Polytechnic University",
        country: "Hong Kong",
        publication_count: 9,
        composite_score: 9.1,
        recruitment_status: "actively_recruiting",
        recruitment_quote: "Postdoc and PhD student positions available in Edge AI and Wireless Distributed Systems.",
        research_topics: ["Edge Computing", "Mobile Edge Intelligence", "Distributed AI"],
        scholar_url: "https://scholar.google.com/citations?user=jcao",
        lab_page: "https://www.polyu.edu.hk/comp/~csjcao/",
        recent_papers: [
          { title: "Collaborative Edge Computing for Next-Generation Distributed AI", venue: "IEEE Communications Magazine", score: 9.2, date: "2026-07-20" }
        ]
      },
      {
        name: "Prof. Mahadev Satyanarayanan",
        institution: "Carnegie Mellon University",
        country: "United States",
        publication_count: 10,
        composite_score: 9.5,
        recruitment_status: "likely_recruiting",
        recruitment_quote: null,
        research_topics: ["Edge Computing", "Cloudlets", "Wearable Cognitive Assistance"],
        scholar_url: "https://scholar.google.com/citations?user=satya",
        lab_page: "https://www.cs.cmu.edu/~satya/",
        recent_papers: [
          { title: "Edge Computing: The Second Decade", venue: "ACM TOCS", score: 9.6, date: "2026-06-10" }
        ]
      }
    ],
    opportunities: [
      {
        title: "PhD Position in Autonomous Edge Intelligence & Distributed Deep Learning",
        university: "Technical University of Munich (TUM)",
        department: "Department of Computer Science",
        country: "Germany",
        supervisor: "Prof. Dr. Hans Weber",
        recruitment_status: "actively_recruiting",
        funding_status: "fully_funded",
        dependant_support: "financially_supported",
        direct_quote: "We are seeking highly motivated PhD students to join our Edge AI group in Fall 2026. Full TV-L E13 funding with child and family allowance is provided.",
        fit_score: 9.7,
        deadline: "2026-11-30",
        link: "https://www.tum.de/phd-edge-ai"
      },
      {
        title: "Hong Kong PhD Fellowship Scheme (HKPFS) in Mobile Edge Computing & 6G",
        university: "Hong Kong University of Science and Technology (HKUST)",
        department: "Department of Computer Science & Engineering",
        country: "Hong Kong",
        supervisor: "Prof. Raymond Liu",
        recruitment_status: "actively_recruiting",
        funding_status: "fully_funded",
        dependant_support: "permitted",
        direct_quote: "Multiple fully funded PhD openings available via HKPFS. Dependants are eligible for student dependant visas.",
        fit_score: 9.5,
        deadline: "2026-12-01",
        link: "https://cerg1.ugc.edu.hk/hkpfs/index.html"
      },
      {
        title: "PhD Studentship in Distributed Systems and Edge-Cloud Orchestration",
        university: "University of Cambridge",
        department: "Computer Laboratory",
        country: "United Kingdom",
        supervisor: "Prof. Alice Smith",
        recruitment_status: "actively_recruiting",
        funding_status: "fully_funded",
        dependant_support: "permitted",
        direct_quote: "Fully funded EPSRC/Gates eligible PhD studentship in Edge-Cloud Systems starting October 2026.",
        fit_score: 9.3,
        deadline: "2026-12-15",
        link: "https://www.cst.cam.ac.uk/phd-positions"
      },
      {
        title: "Funded Doctoral Research in Edge AI & Networking Systems",
        university: "University of Toronto",
        department: "Department of Electrical & Computer Engineering",
        country: "Canada",
        supervisor: "Prof. David Miller",
        recruitment_status: "likely_recruiting",
        funding_status: "fully_funded",
        dependant_support: "financially_supported",
        direct_quote: "Competitive stipend package covering international tuition and living allowance, with open spousal work permit eligibility in Canada.",
        fit_score: 9.2,
        deadline: "2027-01-15",
        link: "https://web.ece.utoronto.ca/grad/phd/"
      }
    ],
    scholarships: [
      {
        name: "DAAD Doctoral Research Grant",
        country: "Germany",
        funding_type: "fully_funded",
        dependant_support: "financially_supported",
        allowance_details: "Dedicated monthly family allowance: ~€276/month spouse allowance + €200/month per child, plus family health insurance subsidy.",
        legal_notes: "Spouse receives German family reunification residence permit with open work permit authorization.",
        deadline: "October - November annually",
        official_link: "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/?status=4&origin=190&subjectGrps=&daadid=57140602&q=&page=1&detail=57140602",
        fit_score: 10.0
      },
      {
        name: "Gates Cambridge Scholarship",
        country: "United Kingdom",
        funding_type: "fully_funded",
        dependant_support: "financially_supported",
        allowance_details: "Family allowance: Up to £11,604 per year for one child and up to £16,548 for two or more children.",
        legal_notes: "UK student visa policy explicitly allows dependants for government/institutionally funded research degree students.",
        deadline: "Early December (international) / Mid-October (US citizens)",
        official_link: "https://www.gatescambridge.org/apply/eligibility/",
        fit_score: 10.0
      },
      {
        name: "Hong Kong PhD Fellowship Scheme (HKPFS)",
        country: "Hong Kong",
        funding_type: "fully_funded",
        dependant_support: "permitted",
        allowance_details: "Generous annual stipend of HK$331,200 (~US$42,460) plus HK$13,800 conference travel allowance per year.",
        legal_notes: "Legal dependant visa permitted for legal spouse and unmarried dependent children under 18.",
        deadline: "December 1 annually",
        official_link: "https://cerg1.ugc.edu.hk/hkpfs/index.html",
        fit_score: 10.0
      },
      {
        name: "Vanier Canada Graduate Scholarships (CGS)",
        country: "Canada",
        funding_type: "fully_funded",
        dependant_support: "financially_supported",
        allowance_details: "Can$50,000 per year for 3 years. Federal Canada Child Benefit (CCB) applies once resident for 18 months.",
        legal_notes: "Spouses of full-time doctoral students in Canada are legally entitled to an Open Work Permit.",
        deadline: "Early November annually",
        official_link: "https://vanier.gc.ca/en/home-accueil.html",
        fit_score: 10.0
      },
      {
        name: "MEXT Japanese Government Doctoral Scholarship",
        country: "Japan",
        funding_type: "fully_funded",
        dependant_support: "permitted",
        allowance_details: "Monthly stipend ~145,000 JPY, full tuition waiver, round-trip airfare. Dependants eligible for Japanese municipal child allowance.",
        legal_notes: "Dependants qualify for 'Dependent' status of residence visa with permission to engage in part-time activity.",
        deadline: "April - May (Embassy track) / October (University track)",
        official_link: "https://www.mext.go.jp/a_menu/koutou/ryugaku/06032818.htm",
        fit_score: 10.0
      },
      {
        name: "UKRI / EPSRC Doctoral Studentship",
        country: "United Kingdom",
        funding_type: "fully_funded",
        dependant_support: "permitted",
        allowance_details: "Full international tuition waiver + minimum tax-free UKRI stipend (£19,237/year).",
        legal_notes: "Government-funded research postgraduate students in the UK are explicitly permitted to bring family dependants.",
        deadline: "Varies by institution (typically Dec - Feb)",
        official_link: "https://www.ukri.org/what-we-offer/developing-people-and-skills/find-studentships-and-doctoral-training/",
        fit_score: 10.0
      },
      {
        name: "Fulbright Foreign Student Program",
        country: "United States",
        funding_type: "fully_funded",
        dependant_support: "permitted",
        allowance_details: "Full tuition, living stipend, health insurance, and travel funding.",
        legal_notes: "Spouse and children travel under J-2 exchange visitor visas. J-2 visa holders can apply for Employment Authorization Document (EAD).",
        deadline: "February - October (varies by home country)",
        official_link: "https://foreign.fulbrightonline.org/",
        fit_score: 10.0
      }
    ],
    target_countries: {
      "Germany": {
        flag: "🇩🇪",
        dependants_permitted: true,
        dependant_support_type: "financially_supported",
        family_allowance_available: true,
        spouse_work_allowed: true,
        official_guidance_url: "https://www.make-it-in-germany.com/en/visa-residence/family-reunification/spouses-joining-non-eu-citizens",
        notes: "Excellent for families: TV-L E13 researcher employment contracts provide health insurance and Kindergeld (~€250/mo per child). Spouses receive unrestricted work rights."
      },
      "Hong Kong": {
        flag: "🇭🇰",
        dependants_permitted: true,
        dependant_support_type: "permitted",
        family_allowance_available: false,
        spouse_work_allowed: false,
        official_guidance_url: "https://www.immd.gov.hk/eng/services/visas/residence_as_dependant.html",
        notes: "Spouse and minor children permitted on Dependant Visas. High HKPFS stipend (HK$331k/yr) comfortably supports family, though spousal employment is restricted on student dependant visas."
      },
      "Canada": {
        flag: "🇨🇦",
        dependants_permitted: true,
        dependant_support_type: "financially_supported",
        family_allowance_available: true,
        spouse_work_allowed: true,
        official_guidance_url: "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/help-your-spouse-common-law-partner-work-canada.html",
        notes: "Family-friendly: Spouses of doctoral students are eligible for open work permits. Children can attend public elementary/secondary school for free. CCB child benefit applies after residency duration."
      },
      "United Kingdom": {
        flag: "🇬🇧",
        dependants_permitted: true,
        dependant_support_type: "permitted",
        family_allowance_available: false,
        spouse_work_allowed: true,
        official_guidance_url: "https://www.gov.uk/student-visa/family-members",
        notes: "The UK Jan 2024 dependant policy changes explicitly PRESERVED dependant rights for PhD and postgraduate research students. Spouses may work full-time."
      },
      "Japan": {
        flag: "🇯🇵",
        dependants_permitted: true,
        dependant_support_type: "permitted",
        family_allowance_available: true,
        spouse_work_allowed: true,
        official_guidance_url: "https://www.isa.go.jp/en/applications/procedures/zairyu_nintei10_19.html",
        notes: "Legal accompaniment on 'Dependent' visa. Jasso/MEXT and Japanese municipal governments provide child allowances (Kodomo Teate). Spouse can work up to 28 hours/week with permission."
      },
      "United States": {
        flag: "🇺🇸",
        dependants_permitted: true,
        dependant_support_type: "permitted",
        family_allowance_available: false,
        spouse_work_allowed: true,
        official_guidance_url: "https://travel.state.gov/content/travel/en/us-visas/study/student-visa.html",
        notes: "Spouse and children eligible for F-2 or J-2 visas. On J-2 visas, spouses are legally eligible to apply for work authorization (EAD)."
      }
    },
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
      }
    ]
  };
  renderAll();
}

function setupEventListeners() {
  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);

  // Tab switching
  const tabButtons = document.querySelectorAll("#tabs-nav .tab-btn");
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const targetTab = btn.getAttribute("data-tab");
      document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));
      const activePane = document.getElementById(`tab-${targetTab}`);
      if (activePane) activePane.classList.add("active");
    });
  });

  // Search input for Feed
  const searchInput = document.getElementById("search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      renderItems();
    });
  }

  // Type pills for Feed
  const typePills = document.querySelectorAll("#type-filters .pill");
  typePills.forEach(pill => {
    pill.addEventListener("click", () => {
      typePills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeType = pill.getAttribute("data-type");
      renderItems();
    });
  });

  // Score selector for Feed
  const scoreSelect = document.getElementById("min-score-select");
  if (scoreSelect) {
    scoreSelect.addEventListener("change", (e) => {
      minScore = parseFloat(e.target.value);
      renderItems();
    });
  }

  // Opportunity filters
  const oppCountrySelect = document.getElementById("opp-country-select");
  if (oppCountrySelect) {
    oppCountrySelect.addEventListener("change", (e) => {
      oppCountryFilter = e.target.value;
      renderOpportunities();
    });
  }

  const oppRecruitmentSelect = document.getElementById("opp-recruitment-select");
  if (oppRecruitmentSelect) {
    oppRecruitmentSelect.addEventListener("change", (e) => {
      oppRecruitmentFilter = e.target.value;
      renderOpportunities();
    });
  }

  const oppFundingSelect = document.getElementById("opp-funding-select");
  if (oppFundingSelect) {
    oppFundingSelect.addEventListener("change", (e) => {
      oppFundingFilter = e.target.value;
      renderOpportunities();
    });
  }

  const oppDependantSelect = document.getElementById("opp-dependant-select");
  if (oppDependantSelect) {
    oppDependantSelect.addEventListener("change", (e) => {
      oppDependantFilter = e.target.value;
      renderOpportunities();
    });
  }

  // Researcher search & filter
  const resSearch = document.getElementById("researcher-search");
  if (resSearch) {
    resSearch.addEventListener("input", (e) => {
      researcherSearch = e.target.value.toLowerCase().trim();
      renderResearchers();
    });
  }

  const resFilterPills = document.querySelectorAll("#researcher-filters .pill");
  resFilterPills.forEach(pill => {
    pill.addEventListener("click", () => {
      resFilterPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      researcherRecruitingFilter = pill.getAttribute("data-filter");
      renderResearchers();
    });
  });
}

function renderAll() {
  renderMeta();
  renderTrends();
  renderSupervisors();
  renderItems();
  renderOpportunities();
  renderResearchers();
  renderScholarships();
  renderCountries();
}

function renderMeta() {
  const meta = dashboardData.meta || {};
  document.getElementById("last-updated").textContent = `Updated: ${meta.last_updated || "Today"}`;
  document.getElementById("metric-total").textContent = meta.total_items || (dashboardData.items ? dashboardData.items.length : 0);
  document.getElementById("metric-high-relevance").textContent = meta.high_relevance_count || 0;
  document.getElementById("metric-recruiting").textContent = meta.active_recruitment_count || 0;
  document.getElementById("metric-opps").textContent = meta.opportunities_count || (dashboardData.opportunities ? dashboardData.opportunities.length : 0);
  document.getElementById("metric-scholarships").textContent = meta.scholarships_count || (dashboardData.scholarships ? dashboardData.scholarships.length : 0);
}

function renderTrends() {
  const container = document.getElementById("trends-list");
  if (!container) return;
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
  if (!container) return;
  container.innerHTML = "";
  const sups = dashboardData.supervisors || [];

  if (sups.length === 0) {
    container.innerHTML = `<div style="font-size: 12px; color: var(--text-muted);">No supervisor data yet.</div>`;
    return;
  }

  sups.slice(0, 5).forEach(s => {
    const isRecruiting = s.recruitment_status === "actively_recruiting";
    const div = document.createElement("div");
    div.className = "supervisor-item";
    div.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: baseline;">
        <span class="supervisor-name">${s.name}</span>
        ${isRecruiting ? '<span class="badge-status badge-recruiting">🟢 Recruiting</span>' : ''}
      </div>
      <div class="supervisor-meta">${s.institution || "Academic Lab"} ${s.country ? `(${s.country})` : ""} &bull; ${s.publication_count || 0} papers</div>
    `;
    container.appendChild(div);
  });
}

function renderItems() {
  const container = document.getElementById("items-container");
  if (!container) return;
  container.innerHTML = "";

  const items = dashboardData.items || [];
  const filtered = items.filter(item => {
    const score = item.score ? item.score.final_score : 0;
    if (score < minScore) return false;

    if (activeType !== "all" && item.item_type !== activeType) {
      if (activeType === "paper" && !["paper", "preprint", "survey"].includes(item.item_type)) {
        return false;
      } else if (activeType !== "paper") {
        return false;
      }
    }

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

function renderOpportunities() {
  const container = document.getElementById("opportunities-container");
  if (!container) return;
  container.innerHTML = "";

  const opps = dashboardData.opportunities || [];
  const filtered = opps.filter(opp => {
    if (oppCountryFilter !== "all" && opp.country !== oppCountryFilter) return false;
    if (oppRecruitmentFilter !== "all" && opp.recruitment_status !== oppRecruitmentFilter) return false;
    if (oppFundingFilter !== "all" && opp.funding_status !== oppFundingFilter) return false;
    if (oppDependantFilter !== "all" && opp.dependant_support !== oppDependantFilter) return false;
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="padding: 40px; text-align: center; color: var(--text-muted); background: var(--bg-card); border-radius: var(--radius-md); grid-column: 1 / -1;">
        <h3>No matching PhD opportunities</h3>
        <p style="font-size: 13px; margin-top: 6px;">Try broadening the country or status filters.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(opp => {
    const card = document.createElement("article");
    card.className = "opp-card";

    let recruitingBadge = '<span class="badge-status badge-unverified">⚪ Open Application</span>';
    if (opp.recruitment_status === "actively_recruiting") {
      recruitingBadge = '<span class="badge-status badge-recruiting">🟢 Actively Recruiting</span>';
    } else if (opp.recruitment_status === "likely_recruiting") {
      recruitingBadge = '<span class="badge-status badge-likely">🟡 Likely Recruiting</span>';
    }

    let fundingBadge = '<span class="badge-status badge-unverified">Funding Unspecified</span>';
    if (opp.funding_status === "fully_funded") {
      fundingBadge = '<span class="badge-status badge-funding">🔵 Fully Funded</span>';
    } else if (opp.funding_status === "partially_funded") {
      fundingBadge = '<span class="badge-status badge-likely">🟡 Partially Funded</span>';
    }

    let dependantBadge = '<span class="badge-status badge-unverified">Dependants Unspecified</span>';
    if (opp.dependant_support === "financially_supported") {
      dependantBadge = '<span class="badge-status badge-dependant">👨‍👩‍👧 Family Financially Supported</span>';
    } else if (opp.dependant_support === "permitted") {
      dependantBadge = '<span class="badge-status badge-permitted">👨‍👩‍👧 Dependants Permitted</span>';
    }

    let quoteHtml = "";
    if (opp.direct_quote) {
      quoteHtml = `<div class="quote-box">&ldquo;${opp.direct_quote}&rdquo;</div>`;
    }

    card.innerHTML = `
      <div class="item-header">
        <a href="${opp.link}" class="card-title" target="_blank" rel="noopener noreferrer">${opp.title}</a>
        ${opp.fit_score ? `<span class="card-score score-good">${opp.fit_score}/10</span>` : ""}
      </div>
      <div class="item-meta">
        <strong>${opp.university}</strong> ${opp.country ? `&bull; 📍 ${opp.country}` : ""}
        ${opp.department ? `&bull; ${opp.department}` : ""}
        ${opp.supervisor ? `&bull; 👤 Supervisor: <strong>${opp.supervisor}</strong>` : ""}
        ${opp.deadline ? `&bull; <strong style="color: var(--accent-red)">Deadline: ${opp.deadline}</strong>` : ""}
      </div>
      <div style="margin: 8px 0;">
        ${recruitingBadge}
        ${fundingBadge}
        ${dependantBadge}
      </div>
      ${quoteHtml}
      ${opp.description ? `<div class="item-abstract" style="margin-top: 8px;">${opp.description.substring(0, 260)}...</div>` : ""}
      <div style="margin-top: 14px;">
        <a href="${opp.link}" class="btn-link" target="_blank" rel="noopener noreferrer">Apply / View Official Posting &rarr;</a>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderResearchers() {
  const container = document.getElementById("researchers-container");
  if (!container) return;
  container.innerHTML = "";

  const researchers = dashboardData.researchers || [];
  const filtered = researchers.filter(r => {
    if (researcherRecruitingFilter === "recruiting" && r.recruitment_status !== "actively_recruiting") {
      return false;
    }
    if (researcherSearch) {
      const name = (r.name || "").toLowerCase();
      const inst = (r.institution || "").toLowerCase();
      const country = (r.country || "").toLowerCase();
      const topics = (r.research_topics || r.topics || []).join(" ").toLowerCase();
      if (!name.includes(researcherSearch) && !inst.includes(researcherSearch) && !country.includes(researcherSearch) && !topics.includes(researcherSearch)) {
        return false;
      }
    }
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="padding: 40px; text-align: center; color: var(--text-muted); background: var(--bg-card); border-radius: var(--radius-md); grid-column: 1 / -1;">
        <h3>No matching researchers found</h3>
        <p style="font-size: 13px; margin-top: 6px;">Try adjusting the search query or status filter.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(r => {
    const card = document.createElement("article");
    card.className = "researcher-card";

    let recruitingBadge = "";
    if (r.recruitment_status === "actively_recruiting") {
      recruitingBadge = '<span class="badge-status badge-recruiting">🟢 Actively Recruiting</span>';
    } else if (r.recruitment_status === "likely_recruiting") {
      recruitingBadge = '<span class="badge-status badge-likely">🟡 Likely Recruiting</span>';
    }

    const topics = r.research_topics || r.topics || [];
    const topicsHtml = topics.map(t => `<span class="topic-pill">${t}</span>`).join("");

    let papersHtml = "";
    if (r.recent_papers && r.recent_papers.length) {
      papersHtml = `
        <div class="recent-papers-box">
          <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">RECENT PUBLICATIONS:</div>
          ${r.recent_papers.slice(0, 3).map(p => `
            <div style="font-size: 12px; margin-bottom: 4px;">
              <a href="${p.url || '#'}" target="_blank" style="color: var(--text-main); text-decoration: none;">&bull; ${p.title}</a>
              <span style="color: var(--text-muted); font-size: 11px;">(${p.venue || "Conference"})</span>
            </div>
          `).join("")}
        </div>
      `;
    }

    let quoteHtml = "";
    if (r.recruitment_quote) {
      quoteHtml = `<div class="quote-box">&ldquo;${r.recruitment_quote}&rdquo;</div>`;
    }

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: baseline;">
        <h3 style="font-size: 17px; font-weight: 700; color: var(--text-main);">${r.name}</h3>
        ${recruitingBadge}
      </div>
      <div class="item-meta" style="margin-top: 4px;">
        <strong>${r.institution || "University"}</strong> ${r.country ? `&bull; 📍 ${r.country}` : ""}
        &bull; 📄 ${r.publication_count || 0} monitored papers
        ${r.composite_score ? `&bull; Fit: <strong>${r.composite_score}/10</strong>` : ""}
      </div>
      ${quoteHtml}
      <div style="margin: 10px 0;">${topicsHtml}</div>
      ${papersHtml}
      <div class="researcher-links" style="margin-top: 12px; font-size: 12px;">
        ${r.lab_page ? `<a href="${r.lab_page}" class="link-btn" target="_blank">🌐 Lab Website</a>` : ""}
        ${r.scholar_url ? `<a href="${r.scholar_url}" class="link-btn" target="_blank">🎓 Google Scholar</a>` : ""}
        ${r.openalex_id ? `<a href="https://openalex.org/authors/${r.openalex_id}" class="link-btn" target="_blank">🔗 OpenAlex</a>` : ""}
      </div>
    `;
    container.appendChild(card);
  });
}

function renderScholarships() {
  const container = document.getElementById("scholarships-container");
  if (!container) return;
  container.innerHTML = "";

  const schols = dashboardData.scholarships || [];
  if (schols.length === 0) {
    container.innerHTML = `<div style="padding: 40px; text-align: center; color: var(--text-muted);">No scholarship data found.</div>`;
    return;
  }

  schols.forEach(s => {
    const card = document.createElement("article");
    card.className = "schol-card";

    let depBadge = "";
    if (s.dependant_support === "financially_supported") {
      depBadge = '<span class="badge-status badge-dependant">👨‍👩‍👧 Dedicated Dependant Allowance</span>';
    } else {
      depBadge = '<span class="badge-status badge-permitted">👨‍👩‍👧 Dependants Permitted</span>';
    }

    card.innerHTML = `
      <div class="item-header">
        <a href="${s.official_link}" class="card-title" target="_blank" rel="noopener noreferrer">${s.name}</a>
        <span class="card-score score-crit">${s.fit_score || 10}/10</span>
      </div>
      <div class="item-meta">
        <strong>Country:</strong> ${s.country} &bull; <strong>Funding:</strong> Fully Funded
        ${s.deadline ? `&bull; <strong style="color: var(--accent-red)">Deadline: ${s.deadline}</strong>` : ""}
      </div>
      <div style="margin: 8px 0;">${depBadge}</div>
      ${s.allowance_details ? `
        <div style="font-size: 13px; color: var(--text-main); margin-bottom: 6px;">
          <strong>Family Allowance:</strong> ${s.allowance_details}
        </div>
      ` : ""}
      ${s.legal_notes ? `
        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">
          <strong>Visa & Work Rights:</strong> ${s.legal_notes}
        </div>
      ` : ""}
      <div style="margin-top: 14px;">
        <a href="${s.official_link}" class="btn-link" target="_blank" rel="noopener noreferrer">Official Application Portal &rarr;</a>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderCountries() {
  const container = document.getElementById("countries-container");
  if (!container) return;
  container.innerHTML = "";

  const countries = dashboardData.target_countries || {};
  const entries = Object.entries(countries);

  if (entries.length === 0) {
    container.innerHTML = `<div style="padding: 40px; text-align: center; color: var(--text-muted);">No country guides loaded.</div>`;
    return;
  }

  entries.forEach(([countryName, info]) => {
    const card = document.createElement("article");
    card.className = "country-card";

    let supportBadge = "";
    if (info.dependant_support_type === "financially_supported") {
      supportBadge = '<span class="badge-status badge-dependant">👨‍👩‍👧 Financially Supported</span>';
    } else {
      supportBadge = '<span class="badge-status badge-permitted">👨‍👩‍👧 Legally Permitted</span>';
    }

    const spouseWork = info.spouse_work_allowed ? "✅ Yes (Open Work Permit or Full-Time Allowed)" : "⚠️ Limited or Special Permission Required";
    const allowanceText = info.family_allowance_available ? "✅ State/Contract Child Allowance Available" : "❌ No Direct State Allowance (Requires Scholarship Allowance)";

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <h3 style="font-size: 18px; font-weight: 700; color: var(--text-main);">${info.flag || "🌍"} ${countryName}</h3>
        ${supportBadge}
      </div>
      <div class="country-detail-row"><strong>Spouse Work Rights:</strong> ${spouseWork}</div>
      <div class="country-detail-row"><strong>Child Allowance Status:</strong> ${allowanceText}</div>
      <div class="item-abstract" style="margin: 10px 0; font-size: 13px;">${info.notes || ""}</div>
      <div style="margin-top: 14px;">
        <a href="${info.official_guidance_url}" class="btn-link" target="_blank" rel="noopener noreferrer">Official Government Visa Portal &rarr;</a>
      </div>
    `;
    container.appendChild(card);
  });
}

