// ─── Navigation configuration ───
// Nav is organized into sections with optional dropdown sub-pages.
const NAV_SECTIONS = [
  { id: "home", href: "index.html", label: "Home" },
  {
    id: "data-preparation-group",
    label: "Data Preparation",
    children: [
      { id: "data-cleaning",    href: "data-cleaning.html",    label: "Data Cleaning" },
      { id: "data-preparation", href: "data-preparation.html", label: "Data Preparation" },
    ],
  },
  { id: "architecture", href: "architecture.html", label: "Architecture" },
  {
    id: "chapters-group",
    label: "Chapters",
    children: [
      { id: "chapter2", href: "chapter2.html", label: "Chapter 2" },
      { id: "chapter3", href: "chapter3.html", label: "Chapter 3" },
      { id: "chapter4", href: "chapter4.html", label: "Chapter 4" },
      { id: "chapter5", href: "chapter5.html", label: "Chapter 5" },
      { id: "chapter6", href: "chapter6.html", label: "Chapter 6" },
    ],
  },
  { id: "records", href: "records.html", label: "Records" },
];

function _isActiveSection(section, pageId) {
  if (section.id === pageId) return true;
  if (section.children) return section.children.some(c => c.id === pageId);
  return false;
}

// ─── Navigation injection ───
function injectNav(pageId) {
  const target = document.getElementById("site-nav");
  if (!target) return;

  const items = NAV_SECTIONS.map(s => {
    if (!s.children) {
      return `<a href="${s.href}" class="nav-link${s.id === pageId ? ' active' : ''}">${s.label}</a>`;
    }
    const active = _isActiveSection(s, pageId);
    const sub = s.children.map(c =>
      `<a href="${c.href}" class="dropdown-item${c.id === pageId ? ' active' : ''}">${c.label}</a>`
    ).join("");
    return `<div class="nav-dropdown${active ? ' active' : ''}">
      <button class="nav-link dropdown-toggle">${s.label}<svg class="chevron" width="10" height="10" viewBox="0 0 10 10"><path d="M2.5 3.5l2.5 3 2.5-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
      <div class="dropdown-menu">${sub}</div>
    </div>`;
  }).join("");

  target.innerHTML = `
    <header class="site-header">
      <a class="logo" href="index.html">Zoobenthic Assessment</a>
      <button class="hamburger" aria-label="Menu" onclick="toggleMobileNav()">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      </button>
      <nav>${items}</nav>
    </header>`;

  // Close dropdowns when clicking elsewhere
  document.addEventListener("click", e => {
    if (!e.target.closest(".nav-dropdown")) {
      document.querySelectorAll(".nav-dropdown.open").forEach(d => d.classList.remove("open"));
    }
  });

  // Toggle dropdowns on click
  document.querySelectorAll(".dropdown-toggle").forEach(btn => {
    btn.addEventListener("click", e => {
      e.stopPropagation();
      const dd = btn.closest(".nav-dropdown");
      const wasOpen = dd.classList.contains("open");
      document.querySelectorAll(".nav-dropdown.open").forEach(d => d.classList.remove("open"));
      if (!wasOpen) dd.classList.add("open");
    });
  });
}

function toggleMobileNav() {
  const nav = document.querySelector(".site-header nav");
  if (nav) nav.classList.toggle("open");
}

// ─── Markdown + MathJax rendering ───
const ENTITY_MAP = { "&": "&amp;", "<": "&lt;", ">": "&gt;" };

function escapeHtml(s) {
  return s.replace(/[&<>]/g, c => ENTITY_MAP[c]);
}

function normalizeMathTeX(s) {
  return s.replace(
    /\\xleftrightarrow\s*\{((?:[^{}]|\{[^{}]*\})*)\}/g,
    (_, label) => "\\mathrel{\\overset{" + label + "}{\\longleftrightarrow}}"
  );
}

function protectMath(source) {
  const segments = [];
  let out = "";
  for (let i = 0; i < source.length;) {
    if (source[i] !== "$") { out += source[i]; i++; continue; }
    const isBlock = source[i + 1] === "$";
    const delim = isBlock ? "$$" : "$";
    const start = i;
    let cursor = i + delim.length;
    let end = -1;
    while (cursor < source.length) {
      if (source[cursor] === "\\") { cursor += 2; continue; }
      if (isBlock ? source.startsWith("$$", cursor) : source[cursor] === "$") { end = cursor; break; }
      cursor++;
    }
    if (end === -1) { out += source[start]; i = start + 1; continue; }
    const token = `@@MATH_${segments.length}@@`;
    segments.push(normalizeMathTeX(source.slice(start, end + delim.length)));
    out += token;
    i = end + delim.length;
  }
  return { protectedSource: out, mathSegments: segments };
}

function restoreMath(html, segments) {
  return html.replace(/@@MATH_(\d+)@@/g, (_, idx) => segments[Number(idx)] ?? "");
}

function renderMarkdown(source) {
  const { protectedSource, mathSegments } = protectMath(source);
  if (!window.marked) return `<pre>${escapeHtml(source)}</pre>`;
  const html = window.marked.parse(protectedSource, { gfm: true, breaks: false });
  return restoreMath(html, mathSegments);
}

// ─── Cell rendering ───
function renderCells(cells) {
  const container = document.getElementById("notebook");
  if (!container || !cells) return;
  container.innerHTML = "";

  for (const cell of cells) {
    const section = document.createElement("section");
    section.className = "cell";
    const body = document.createElement("div");
    if (cell.cell_type === "markdown") {
      body.innerHTML = renderMarkdown(cell.source);
    } else {
      body.innerHTML = `<pre><code>${escapeHtml(cell.source)}</code></pre>`;
    }
    section.appendChild(body);
    container.appendChild(section);
  }

  if (window.MathJax && window.MathJax.typesetPromise) {
    window.MathJax.typesetPromise();
  }
}

// ─── Sidebar TOC generation ───
function buildTOC() {
  const sidebar = document.getElementById("sidebar");
  const content = document.getElementById("notebook") || document.querySelector(".content-area");
  if (!sidebar || !content) return;

  const headings = content.querySelectorAll("h1, h2, h3, h4");
  if (headings.length === 0) { sidebar.style.display = "none"; return; }

  headings.forEach((h, i) => {
    if (!h.id) h.id = "section-" + i;
  });

  let html = '<p class="sidebar-title">On this page</p><ul>';
  headings.forEach(h => {
    const cls = `toc-${h.tagName.toLowerCase()}`;
    html += `<li><a href="#${h.id}" class="${cls}">${h.textContent}</a></li>`;
  });
  html += "</ul>";
  sidebar.innerHTML = html;

  // IntersectionObserver for active highlighting
  const links = sidebar.querySelectorAll("a");
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        links.forEach(l => l.classList.remove("toc-active"));
        const active = sidebar.querySelector(`a[href="#${entry.target.id}"]`);
        if (active) active.classList.add("toc-active");
      }
    }
  }, { rootMargin: `-${parseInt(getComputedStyle(document.documentElement).getPropertyValue("--header-h")) + 20}px 0px -60% 0px`, threshold: 0 });

  headings.forEach(h => observer.observe(h));

  // Sidebar toggle for mobile
  const toggleBtn = document.querySelector(".sidebar-toggle");
  const overlay = document.querySelector(".sidebar-overlay");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      if (overlay) overlay.classList.toggle("open");
    });
  }
  if (overlay) {
    overlay.addEventListener("click", () => {
      sidebar.classList.remove("open");
      overlay.classList.remove("open");
    });
  }
}

// ─── Initialize ───
function waitForMarked(cb, tries) {
  if (window.marked || tries > 20) { cb(); return; }
  setTimeout(() => waitForMarked(cb, tries + 1), 100);
}

window.addEventListener("DOMContentLoaded", () => {
  const pageId = window.PAGE_ID || "home";
  injectNav(pageId);

  if (window.cells) {
    waitForMarked(() => {
      renderCells(window.cells);
      buildTOC();
    }, 0);
  } else {
    buildTOC();
  }
});
