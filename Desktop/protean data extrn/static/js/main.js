// static/js/main.js

const countrySelect = document.getElementById("countrySelect");
const siteSelect = document.getElementById("siteSelect");
const viewBtn = document.getElementById("viewBtn");
const refreshBtn = document.getElementById("refreshBtn");
const demoFillBtn = document.getElementById("demoFillBtn");

const setLoading = (el, isLoading, placeholderText) => {
  if (isLoading) {
    el.innerHTML = `<option value="">${placeholderText || 'Loading...'}</option>`;
    el.disabled = true;
  } else {
    el.disabled = false;
  }
};

async function fetchCountries() {
  setLoading(countrySelect, true, "Loading countries...");
  try {
    const res = await fetch("/api/countries");
    const data = await res.json();
    countrySelect.innerHTML = `<option value="">-- Select country --</option>`;
    data.countries.forEach(c => {
      const o = document.createElement("option");
      o.value = c;
      o.textContent = c;
      countrySelect.appendChild(o);
    });
    countrySelect.disabled = false;
  } catch (err) {
    console.error(err);
    countrySelect.innerHTML = `<option value="">Error loading</option>`;
  }
}

async function fetchSites(country) {
  setLoading(siteSelect, true, "Loading sites...");
  try {
    const res = await fetch(`/api/sites?country=${encodeURIComponent(country)}`);
    const data = await res.json();
    siteSelect.innerHTML = `<option value="">-- Select website --</option>`;
    if (!data.sites || data.sites.length === 0) {
      siteSelect.innerHTML = `<option value="">No sites found for ${country}</option>`;
      siteSelect.disabled = true;
      viewBtn.disabled = true;
      return;
    }
    data.sites.forEach(s => {
      const o = document.createElement("option");
      o.value = s.domain;
      o.textContent = `${s.name} — ${s.domain}`;
      siteSelect.appendChild(o);
    });
    siteSelect.disabled = false;
    viewBtn.disabled = false;
  } catch (err) {
    console.error(err);
    siteSelect.innerHTML = `<option value="">Error loading sites</option>`;
  }
}

async function fetchSiteInfo(domain) {
  // Show quick loading placeholders
  document.getElementById("siteName").textContent = "Loading site info...";
  document.getElementById("siteDomain").textContent = domain;
  document.getElementById("siteDescription").textContent = "";
  try {
    const res = await fetch(`/api/site_info?domain=${encodeURIComponent(domain)}`);
    const data = await res.json();
    const s = data.site;
    // populate UI
    document.getElementById("siteName").textContent = s.name || s.domain;
    document.getElementById("siteDomain").textContent = s.domain || "";
    document.getElementById("siteDescription").textContent = s.description || "-";
    document.getElementById("siteFounded").textContent = s.founded || "-";
    document.getElementById("siteVisitors").textContent = s.monthly_visitors_est || "-";
    document.getElementById("siteGlobalRank").textContent = s.global_rank || "-";
    document.getElementById("siteCountryRank").textContent = s.country_rank || "-";
    document.getElementById("siteCategories").textContent = (s.top_categories || []).join(", ") || "-";
    document.getElementById("sitePayments").textContent = (s.payment_methods || []).join(", ") || "-";
    document.getElementById("siteShipping").textContent = (s.shipping_options || []).join(", ") || "-";
    document.getElementById("siteReturns").textContent = s.return_policy || "-";
    document.getElementById("techStack").textContent = (s.tech_stack || []).join(" • ") || "-";

    const topProducts = document.getElementById("topProducts");
    topProducts.innerHTML = "";
    (s.sample_top_products || []).forEach(p => {
      const li = document.createElement("li");
      li.textContent = `${p.title} — ${p.price || ""}`;
      topProducts.appendChild(li);
    });

  } catch (err) {
    console.error(err);
    document.getElementById("siteName").textContent = "Error loading site info";
    document.getElementById("siteDescription").textContent = "";
  }
}

// event listeners
countrySelect.addEventListener("change", (e) => {
  const country = e.target.value;
  if (!country) {
    siteSelect.innerHTML = `<option value="">Select a country first</option>`;
    siteSelect.disabled = true;
    viewBtn.disabled = true;
    return;
  }
  fetchSites(country);
});

viewBtn.addEventListener("click", () => {
  const domain = siteSelect.value;
  if (!domain) return alert("Select a site");
  fetchSiteInfo(domain);
});

refreshBtn.addEventListener("click", () => {
  fetchCountries();
  siteSelect.innerHTML = `<option value="">Select a country first</option>`;
  siteSelect.disabled = true;
  viewBtn.disabled = true;
});

demoFillBtn.addEventListener("click", () => {
  countrySelect.value = "Ghana";
  fetchSites("Ghana");
});

// initial load
fetchCountries();
