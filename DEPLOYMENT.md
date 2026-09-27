# Deployment Guide

## GitHub Pages Deployment

### Setup

1. Create a new GitHub repository for the website
2. Push the local repository to GitHub:

```bash
git init
git add .
git commit -m "Initial commit: MkDocs website for NuTS"
git remote add origin https://github.com/YOUR_USERNAME/nuts-website.git
git push -u origin main
```

### Deploy to GitHub Pages

Deploy the site using MkDocs built-in gh-deploy command:

```bash
uv run mkdocs gh-deploy
```

This will:
- Build the site
- Create/update a `gh-pages` branch
- Push the built site to GitHub
- Make it available at `https://YOUR_USERNAME.github.io/nuts-website/`

### Custom Domain

To use a custom domain:

1. Add a `CNAME` file in the `docs/` directory with your domain:
   ```
   nuts.your-domain.fr
   ```

2. Configure your DNS settings to point to GitHub Pages

3. Enable custom domain in repository settings

## GitLab Pages Deployment

If you prefer GitLab, create a `.gitlab-ci.yml` file:

```yaml
pages:
  image: python:3.11
  before_script:
    - pip install uv
    - uv sync
  script:
    - uv run mkdocs build --strict
    - mv site public
  artifacts:
    paths:
      - public
  only:
    - main
```

## Local Preview

Always preview changes locally before deploying:

```bash
uv run mkdocs serve
```

Visit http://127.0.0.1:8000/ to see the site.

## Continuous Integration

The site can be automatically deployed on every push using GitHub Actions. Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy MkDocs

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install UV
        run: pip install uv
      
      - name: Install dependencies
        run: uv sync
      
      - name: Deploy
        run: uv run mkdocs gh-deploy --force
```

## Updating Content

1. Edit markdown files in `docs/`
2. Preview locally with `uv run mkdocs serve`
3. Commit and push changes
4. Deploy with `uv run mkdocs gh-deploy` (or let CI/CD handle it)
