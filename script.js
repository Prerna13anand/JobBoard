/*
 * Job board frontend - Milestone 5.
 *
 * Loads the aggregated jobs.json produced by the Python pipeline, renders
 * it as a grid of cards, and supports live (debounced) text search, a
 * location filter, and sorting. The pipeline is: load -> filter (search +
 * location) -> sort -> render, implemented as small composable functions
 * (`applyFilters`, `applySort`) so it stays easy to extend.
 */

const JOBS_URL = "jobs.json";
const MAX_VISIBLE_TAGS = 6;
const SEARCH_DEBOUNCE_MS = 280;

const jobCountEl = document.getElementById("jobCount");
const statusEl = document.getElementById("statusMessage");
const jobGridEl = document.getElementById("jobGrid");
const searchInputEl = document.getElementById("searchInput");
const locationSelectEl = document.getElementById("locationSelect");
const sortSelectEl = document.getElementById("sortSelect");
const clearFiltersBtnEl = document.getElementById("clearFiltersBtn");

// Holds all loaded jobs plus whatever filter/sort criteria are active.
// Further milestones can add more keys to `filters` without changing how
// `applyFilters`/`applySort`/`updateView` are wired up.
const state = {
  allJobs: [],
  filters: {
    search: "",
    location: "",
    sort: "newest",
  },
};

/** Escape a value for safe insertion into HTML text/attribute content. */
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** Only allow http(s) URLs through to href attributes. */
function safeUrl(url) {
  return typeof url === "string" && /^https?:\/\//i.test(url) ? url : "#";
}

/** Build the HTML for a single job's tag badges, capped so cards stay a consistent size. */
function buildTagsHtml(tags) {
  const list = Array.isArray(tags) ? tags : [];
  const visible = list.slice(0, MAX_VISIBLE_TAGS);
  const remaining = list.length - visible.length;

  const badges = visible.map((tag) => `<span class="badge badge-tag">${escapeHtml(tag)}</span>`);
  if (remaining > 0) {
    badges.push(`<span class="badge badge-tag badge-tag-more">+${remaining}</span>`);
  }
  return badges.join("");
}

/** Build the HTML for a single job card. */
function buildJobCardHtml(job) {
  const title = escapeHtml(job.title || "Untitled position");
  const company = escapeHtml(job.company || "Unknown company");
  const location = escapeHtml(job.location || "Location not specified");
  const posted = escapeHtml(job.posted || "Date unknown");
  const url = escapeHtml(safeUrl(job.url));
  const remoteBadge = job.remote
    ? '<span class="badge badge-remote">Remote</span>'
    : '<span class="badge badge-onsite">On-site</span>';

  return `
    <article class="job-card">
      <div class="job-card-header">
        <a class="job-title" href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>
        ${remoteBadge}
      </div>
      <p class="job-company">${company}</p>
      <p class="job-location">${location}</p>
      <div class="job-tags">${buildTagsHtml(job.tags)}</div>
      <p class="job-posted">Posted: ${posted}</p>
    </article>
  `;
}

/** Render the live job count header, e.g. "15,913 jobs". */
function renderJobCount(count) {
  jobCountEl.textContent = `${count.toLocaleString()} jobs`;
}

/** Render all job cards in a single DOM write, reusing precomputed HTML per job. */
function renderJobs(jobs) {
  const html = jobs.map((job) => job._cardHtml).join("");
  jobGridEl.innerHTML = html;
}

/** Show or clear the status area (used for loading/error/empty-results states). */
function setStatus(message, isError = false) {
  statusEl.textContent = message || "";
  statusEl.classList.toggle("error", isError);
}

/**
 * Precompute, once per job at load time: a lowercased blob of searchable
 * text (title, company, tags), a lowercased title for sorting, and the
 * job's rendered card HTML. Filtering/sorting then only touch these
 * precomputed fields, and rendering only joins already-built `_cardHtml`
 * strings, instead of redoing that work on every keystroke. Keeps live
 * search and sort fast at ~16,000 jobs.
 */
function withSearchIndex(job) {
  const searchableParts = [job.title, job.company, ...(Array.isArray(job.tags) ? job.tags : [])];
  return {
    ...job,
    _searchText: searchableParts.filter(Boolean).join(" ").toLowerCase(),
    _titleLower: (job.title || "").toLowerCase(),
    _cardHtml: buildJobCardHtml(job),
  };
}

/** Does this job match the current search query? */
function matchesSearch(job, query) {
  return !query || job._searchText.includes(query);
}

/** Does this job match the currently selected location (exact match, "" = all locations)? */
function matchesLocation(job, location) {
  return !location || job.location === location;
}

/**
 * Apply every active filter to the job list. New filter types (remote-only,
 * etc.) can be added here as additional checks without touching the
 * callers.
 */
function applyFilters(jobs, filters) {
  const query = filters.search.trim().toLowerCase();
  const location = filters.location;

  if (!query && !location) {
    return jobs;
  }

  return jobs.filter((job) => matchesSearch(job, query) && matchesLocation(job, location));
}

/**
 * Sort a job list without mutating the array passed in (it may be the
 * same reference as `state.allJobs` when no filters are active).
 * "newest" compares the already ISO "YYYY-MM-DD" `posted` strings
 * directly, since plain string comparison sorts them chronologically.
 */
function applySort(jobs, sortBy) {
  const sorted = jobs.slice();

  if (sortBy === "title-asc") {
    sorted.sort((a, b) => (a._titleLower < b._titleLower ? -1 : a._titleLower > b._titleLower ? 1 : 0));
  } else {
    sorted.sort((a, b) => (a.posted > b.posted ? -1 : a.posted < b.posted ? 1 : 0));
  }

  return sorted;
}

/** Re-run filters + sorting over all jobs and update the count, grid, and status message. */
function updateView() {
  const filteredJobs = applyFilters(state.allJobs, state.filters);
  const sortedJobs = applySort(filteredJobs, state.filters.sort);

  renderJobCount(sortedJobs.length);

  if (sortedJobs.length === 0) {
    jobGridEl.innerHTML = "";
    setStatus("No jobs found.");
    return;
  }

  setStatus("");
  renderJobs(sortedJobs);
}

/** Fetch and parse jobs.json. */
async function loadJobs() {
  const response = await fetch(JOBS_URL);
  if (!response.ok) {
    throw new Error(`Failed to load ${JOBS_URL}: HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * Wrap `fn` so rapid repeated calls collapse into one call `delay`ms after
 * the last one. Exposes `.cancel()` so a pending call can be dropped (e.g.
 * when Clear Filters already forces an immediate, up-to-date render).
 */
function debounce(fn, delay) {
  let timeoutId;

  function debounced(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  }

  debounced.cancel = () => clearTimeout(timeoutId);
  return debounced;
}

const debouncedUpdateView = debounce(updateView, SEARCH_DEBOUNCE_MS);

function setupSearch() {
  searchInputEl.addEventListener("input", (event) => {
    state.filters.search = event.target.value;
    debouncedUpdateView();
  });
}

/** Fill the location dropdown with every unique location found in the dataset, A-Z. */
function populateLocationOptions(jobs) {
  const uniqueLocations = Array.from(new Set(jobs.map((job) => job.location).filter(Boolean))).sort(
    (a, b) => a.localeCompare(b)
  );

  const optionsHtml = uniqueLocations
    .map((location) => `<option value="${escapeHtml(location)}">${escapeHtml(location)}</option>`)
    .join("");

  locationSelectEl.insertAdjacentHTML("beforeend", optionsHtml);
}

function setupLocationFilter() {
  locationSelectEl.addEventListener("change", (event) => {
    state.filters.location = event.target.value;
    updateView();
  });
}

function setupSort() {
  sortSelectEl.addEventListener("change", (event) => {
    state.filters.sort = event.target.value;
    updateView();
  });
}

function setupClearFilters() {
  clearFiltersBtnEl.addEventListener("click", () => {
    debouncedUpdateView.cancel();

    searchInputEl.value = "";
    locationSelectEl.value = "";
    sortSelectEl.value = "newest";
    state.filters.search = "";
    state.filters.location = "";
    state.filters.sort = "newest";

    updateView();
  });
}

/** Entry point: load jobs, then render the count and the grid. */
async function init() {
  setStatus("Loading jobs...");
  setupSearch();
  setupLocationFilter();
  setupSort();
  setupClearFilters();

  try {
    const jobs = await loadJobs();
    state.allJobs = jobs.map(withSearchIndex);
    populateLocationOptions(state.allJobs);
    updateView();
  } catch (error) {
    console.error(error);
    setStatus("Failed to load jobs. Please try again later.", true);
    jobCountEl.textContent = "";
  }
}

init();
