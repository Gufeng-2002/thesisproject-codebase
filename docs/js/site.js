// ─── Navigation configuration ───
// To add a new page: add one entry here and create the HTML file.
const NAV_PAGES = [
  { id: "home",             href: "index.html",            label: "Home" },
  { id: "data-cleaning",    href: "data-cleaning.html",    label: "Data Cleaning" },
  { id: "data-preparation", href: "data-preparation.html", label: "Data Preparation" },
  { id: "workflow",         href: "workflow.html",          label: "Workflow" },
  { id: "chapter2",         href: "chapter2.html",         label: "Ch.2: Pollution" },
  { id: "chapter3",         href: "chapter3.html",         label: "Ch.3: Standardization" },
];

// ─── Navigation injection ───
function injectNav(pageId) {
  const target = document.getElementById("site-nav");
  if (!target) return;

  const links = NAV_PAGES.map(p =>
    `<a href="${p.href}" class="${p.id === pageId ? 'active' : ''}">${p.label}</a>`
  ).join("");

  target.innerHTML = `
    <header class="site-header">
      <a class="logo" href="index.html">Zoobenthic Assessment</a>
      <button class="hamburger" aria-label="Menu" onclick="toggleMobileNav()">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      </button>
      <nav>${links}</nav>
    </header>`;
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

  const headings = content.querySelectorAll("h2, h3");
  if (headings.length === 0) { sidebar.style.display = "none"; return; }

  headings.forEach((h, i) => {
    if (!h.id) h.id = "section-" + i;
  });

  let html = '<p class="sidebar-title">On this page</p><ul>';
  headings.forEach(h => {
    const cls = h.tagName === "H3" ? "toc-h3" : "";
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
