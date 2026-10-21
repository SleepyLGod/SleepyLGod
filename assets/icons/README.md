# Vendored tool icons

These SVGs are checked into the repository so the profile does not depend on an
icon CDN at viewing time.

- Devicon **v2.17.0**: C, C++, Python, Java, Go, TypeScript, Node.js, Linux, Git,
  Neovim, PostgreSQL, Redis, Docker, Kubernetes, PyTorch, TensorFlow, Pandas, Neo4j.
  Source: <https://github.com/devicons/devicon/tree/v2.17.0/icons>.
  License: `LICENSE-devicon.txt`.
- Simple Icons **15.16.0**: NVIDIA, OpenAI, Google Gemini, Claude, LangGraph.
  Source: <https://www.npmjs.com/package/simple-icons/v/15.16.0>.
  License: `LICENSE-simple-icons.md`. A display fill color has been added to these
  monochrome SVGs for visibility on light and dark backgrounds.
- The Rust PNG is an existing repository file at `icons/rust.png`.

Brand names and logos belong to their respective owners. SVG paths are unmodified.

`pandas-dark.svg` and `neo4j-dark.svg` lighten dark fills for contrast on dark
backgrounds. Only colors change; their SVG paths remain the same.

## Active animated toolbox

The visible README uses `animated/*.svg`. `scripts/build_tool_icons.py` combines
the cached monochrome logos with the original **readme-components** layout and
CSS, including its **4s linear infinite** spin and black rounded badge.

- Renderer source: <https://github.com/harish-sethuraman/readme-components/tree/923a60dead6c960276d3cf78d7100c82f9d9dfbe/src/logo-component>.
- Its MIT license is retained in `LICENSE-readme-components.txt`.
- `animated/style.css` is the upstream CSS rendered with the original black fill
  and purple logo color. The generator substitutes the per-icon purple colors
  and adds a reduced-motion override.
- `animated/icons.json` records each logo's source and color. Most original logos
  come from **simple-icons@3.5.0**, the upstream component's declared dependency;
  its CC0 license is in `LICENSE-simple-icons-3.5.md`.
- Newer Gemini, Claude, and LangGraph logos use the already vendored
  **simple-icons@15.16.0** data. Sources are cached in `monochrome/`.

The renderer outputs are committed files. Viewing the profile makes no requests
to the original Vercel service and needs no package installation.
