from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "Skeleton.ipynb"
OUTPUT_DIR = ROOT / "docs"
OUTPUT_PATH = OUTPUT_DIR / "index.html"
NOJEKYLL_PATH = OUTPUT_DIR / ".nojekyll"


def _normalize_source(source: object) -> str:
    if isinstance(source, list):
        pieces: list[str] = []
        for item in source:
            text = str(item)
            pieces.append(text if text.endswith("\n") else f"{text}\n")
        return "".join(pieces).rstrip()
    return str(source).rstrip()


def _load_cells(notebook_path: Path) -> list[dict[str, str]]:
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells: list[dict[str, str]] = []

    for cell in notebook.get("cells", []):
        source = _normalize_source(cell.get("source", []))
        if not source.strip():
            continue

        cell_type = str(cell.get("cell_type", "")).strip().lower()
        if cell_type not in {"markdown", "code"}:
            continue

        language = ""
        metadata = cell.get("metadata", {})
        if isinstance(metadata, dict):
            language = str(metadata.get("language", "")).strip().lower()

        cells.append(
            {
                "cell_type": cell_type,
                "language": language or "text",
                "source": source,
            }
        )

    return cells


def _infer_title(cells: list[dict[str, str]]) -> str:
    heading_pattern = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
    for cell in cells:
        if cell["cell_type"] != "markdown":
            continue
        match = heading_pattern.search(cell["source"])
        if match:
            return match.group(1)
    return NOTEBOOK_PATH.stem


def _build_html(title: str, cells: list[dict[str, str]]) -> str:
    page_title = escape(title)
    notebook_name = escape(NOTEBOOK_PATH.name)
    serialized_cells = json.dumps(cells, ensure_ascii=True)

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{page_title}</title>
  <meta name=\"description\" content=\"Static website generated from {notebook_name}.\">
  <style>
    :root {{
      color-scheme: light;
      --bg: #ffffff;
      --page: #ffffff;
      --ink: #22201c;
      --muted: #5f5f5f;
      --rule: #d8d8d8;
      --code: #ffffff;
      --accent: #22201c;
    }}

    * {{ box-sizing: border-box; }}

    html {{ scroll-behavior: smooth; }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      font-size: 14px;
      line-height: 1.6;
    }}

    main {{
      width: min(100%, 980px);
      margin: 0 auto;
      padding: 36px 28px 60px;
    }}

    h1, h2, h3, h4, h5, h6 {{
      line-height: 1.25;
      margin: 1.1em 0 0.45em;
      color: #181614;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      font-weight: 500;
    }}

    h1 {{
      margin-top: 0;
      font-size: clamp(1.8rem, 3vw, 2.2rem);
      letter-spacing: -0.01em;
    }}

    h2 {{ font-size: clamp(1.5rem, 2.4vw, 1.75rem); }}
    h3 {{ font-size: clamp(1.16rem, 2vw, 1.32rem); }}
    h4, h5, h6 {{ font-size: 1rem; }}

    p, li {{ font-size: 1rem; }}

    p {{ margin: 0 0 1rem; }}

    ul, ol {{
      margin: 0 0 1rem;
      padding-left: 2rem;
    }}

    li + li {{ margin-top: 0.35rem; }}

    a {{
      color: var(--accent);
      text-decoration-thickness: 1px;
      text-underline-offset: 0.14em;
    }}

    .notebook {{ display: block; }}

    .cell {{
      background: var(--page);
      padding: 0;
    }}

    .cell + .cell {{ margin-top: 0; }}

    .cell > :first-child {{ margin-top: 0; }}
    .cell > :last-child {{ margin-bottom: 0; }}

    pre {{
      overflow-x: auto;
      padding: 12px 0 12px 14px;
      border: 1px solid var(--rule);
      background: var(--code);
      font-size: 0.92rem;
      line-height: 1.55;
    }}

    code {{
      font-family: Menlo, Consolas, "DejaVu Sans Mono", monospace;
      background: #eeeeee;
      padding: 1px 5px;
      border-radius: 0;
      font-size: 0.92em;
    }}

    pre code {{
      background: transparent;
      padding: 0;
      border-radius: 0;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      display: block;
      overflow-x: auto;
      margin: 1.25rem 0;
    }}

    th, td {{
      border: 1px solid var(--rule);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }}

    th {{ background: #ffffff; }}

    blockquote {{
      margin: 1.2rem 0;
      padding-left: 1rem;
      border-left: 3px solid var(--rule);
      color: var(--muted);
    }}

    img {{ max-width: 100%; height: auto; }}

    hr {{ border: 0; border-top: 1px solid var(--rule); }}

    @media (max-width: 700px) {{
      main {{ padding: 24px 16px 44px; }}
      p, li {{ font-size: 1rem; }}
    }}
  </style>
  <script>
    window.MathJax = {{
      loader: {{ load: ['[tex]/extpfeil'] }},
      tex: {{
        packages: {{ '[+]': ['extpfeil'] }},
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']]
      }},
      svg: {{ fontCache: 'global' }}
    }};
  </script>
  <script defer src=\"https://cdn.jsdelivr.net/npm/marked/marked.min.js\"></script>
  <script defer src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js\"></script>
</head>
<body>
  <main>
    <div id=\"notebook\" class=\"notebook\"></div>
  </main>
  <script>
    const cells = {serialized_cells};
    const entityMap = {{ '&': '&amp;', '<': '&lt;', '>': '&gt;' }};

    function escapeHtml(source) {{
      return source.replace(/[&<>]/g, (char) => entityMap[char]);
    }}

    function normalizeMathTeX(source) {{
      return source.replace(
        /\\\\xleftrightarrow\\s*\\{{((?:[^{{}}]|\\{{[^{{}}]*\\}})*)\\}}/g,
        (_, label) => '\\\\mathrel{{\\\\overset{{' + label + '}}{{\\\\longleftrightarrow}}}}'
      );
    }}

    function protectMath(source) {{
      const mathSegments = [];
      let protectedSource = '';

      for (let index = 0; index < source.length;) {{
        if (source[index] !== '$') {{
          protectedSource += source[index];
          index += 1;
          continue;
        }}

        const isBlock = source[index + 1] === '$';
        const delimiter = isBlock ? '$$' : '$';
        const start = index;
        let cursor = index + delimiter.length;
        let end = -1;

        while (cursor < source.length) {{
          if (source[cursor] === '\\\\') {{
            cursor += 2;
            continue;
          }}

          if (isBlock ? source.startsWith('$$', cursor) : source[cursor] === '$') {{
            end = cursor;
            break;
          }}

          cursor += 1;
        }}

        if (end === -1) {{
          protectedSource += source[start];
          index = start + 1;
          continue;
        }}

        const token = `@@MATH_${{mathSegments.length}}@@`;
        mathSegments.push(normalizeMathTeX(source.slice(start, end + delimiter.length)));
        protectedSource += token;
        index = end + delimiter.length;
      }}

      return {{ protectedSource, mathSegments }};
    }}

    function restoreMath(html, mathSegments) {{
      return html.replace(/@@MATH_(\\d+)@@/g, (_, index) => mathSegments[Number(index)] ?? '');
    }}

    function renderMarkdown(source) {{
      const {{ protectedSource, mathSegments }} = protectMath(source);
      if (!window.marked) {{
        return `<pre>${{escapeHtml(source)}}</pre>`;
      }}
      const rendered = window.marked.parse(protectedSource, {{ gfm: true, breaks: false, mangle: false, headerIds: true }});
      return restoreMath(rendered, mathSegments);
    }}

    function renderNotebook() {{
      const container = document.getElementById('notebook');
      container.replaceChildren();

      for (const cell of cells) {{
        const section = document.createElement('section');
        section.className = 'cell';

        const body = document.createElement('div');
        if (cell.cell_type === 'markdown') {{
          body.innerHTML = renderMarkdown(cell.source);
        }} else {{
          body.innerHTML = `<pre><code>${{escapeHtml(cell.source)}}</code></pre>`;
        }}
        section.appendChild(body);
        container.appendChild(section);
      }}

      if (window.MathJax && window.MathJax.typesetPromise) {{
        window.MathJax.typesetPromise();
      }}
    }}

    window.addEventListener('DOMContentLoaded', renderNotebook);
  </script>
</body>
</html>
"""


def main() -> None:
    cells = _load_cells(NOTEBOOK_PATH)
    title = _infer_title(cells)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(_build_html(title, cells), encoding="utf-8")
    NOJEKYLL_PATH.write_text("", encoding="utf-8")

    print(f"Loaded cells: {len(cells)}")
    print(f"Wrote website: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()