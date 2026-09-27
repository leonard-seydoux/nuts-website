# NuTS Website

This repository contains the MkDocs-based website for **NuTS** (Numérique pour la Terre Solide), the INSU thematic network dedicated to numerical methods in solid Earth sciences.

## About NuTS

Le réseau thématique (RT) *Numérique en Terre Solide* (NuTS) vise à structurer la communauté des développeurs et utilisateurs du numérique en Terre Solide (TS) avec pour objectifs de la rendre plus visible, plus efficace et mieux informée.

## Development

This website is built using [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/).

### Prerequisites

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) package manager

### Installation

Install dependencies using UV:

```bash
uv sync
```

### Building the site

Build the static site:

```bash
uv run mkdocs build
```

### Serving locally

Run a local development server:

```bash
uv run mkdocs serve
```

The site will be available at `http://127.0.0.1:8000/`

### Deploying

To deploy to GitHub Pages:

```bash
uv run mkdocs gh-deploy
```

## Content Structure

- `docs/` - Markdown source files for the website
  - `index.md` - Homepage
  - `context.md` - Context and background
  - `objectifs.md` - Objectives
  - `actions.md` - Actions and resources overview
  - `organisation.md` - Organization and participants
  - `kickoff.md` - Kickoff meeting (2022)
  - `workshop1.md` - Workshop 1 (2023) - Machine Learning
  - `workshop2.md` - Workshop 2 (2024) - Inverse Problems
  - `workshop3.md` - Workshop 3 (2025) - Grenoble
  - `images/` - Image assets
- `mkdocs.yml` - MkDocs configuration file
- `site/` - Generated static site (excluded from git)

## License

Copyright © 2022-2026 NuTS. Tous droits réservés.

Original content from [nuts.univ-nantes.io](https://nuts.univ-nantes.io/)
