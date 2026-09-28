# Site web de NuTS

Site du réseau thématique **NuTS** (*Numérique en Terre Solide*) de l'INSU, construit avec [MkDocs](https://www.mkdocs.org/) et le thème [Material](https://squidfunk.github.io/mkdocs-material/).

Version temporaire en ligne : <https://leonard-seydoux.github.io/nuts-website/>

## Développement

Prérequis : Python 3.11+ et [uv](https://docs.astral.sh/uv/).

```bash
uv sync                  # installe les dépendances
uv run mkdocs serve --watch overrides --watch hooks
```

Le site est servi sur <http://127.0.0.1:8000/nuts-website/> (le chemin vient de `site_url` dans `mkdocs.yml`) et se recharge à chaque modification des pages, des gabarits et des hooks.

Pour vérifier que tout se construit sans erreur :

```bash
uv run mkdocs build --strict
```

## Organisation

| Dossier | Contenu |
|---------|---------|
| `docs/` | pages Markdown, images, vidéos, CSS (`stylesheets/extra.css`) et JS |
| `docs/workshops/` | une page par rencontre, et la frise des rencontres (`index.md`) |
| `docs/blog/posts/` | articles du blog (synthèses des groupes de discussion…) |
| `overrides/` | gabarits Material : page d'accueil et son hero (`home.html`), bandeau des pages (`main.html`), en-tête, logo, pied de page |
| `hooks/` | transformations des pages : cartes et frise (`list_cards.py`), sections texte et image (`figure_sections.py`), vidéos transparentes (`alpha_videos.py`), barres latérales masquées (`sidebars.py`) |
| `illustrations/` | scripts matplotlib des globes animés et du logo (projet uv séparé) |

## Ajouter du contenu

**Une rencontre.** Créer `docs/workshops/<nom>.md` (en-tête `description:` pour le bandeau), l'ajouter à `nav` dans `mkdocs.yml` et à la frise de `docs/workshops/index.md`. Dans la frise, les pages `workshop-*` et `kickoff-*` ont un carré (rencontres plénières), les autres un `+`.

**Un article de blog.** Créer `docs/blog/posts/<nom>.md` avec `date:` et `slug:` dans l'en-tête, et `<!-- more -->` après le chapeau. Le relier depuis la page de la rencontre concernée si besoin.

**Les boutons d'annonce du hero** (prochaines rencontres) sont écrits en dur dans `overrides/home.html` : à mettre à jour une fois les rencontres passées.

## Illustrations

Les globes sont des vidéos transparentes rendues en ASCII par matplotlib, dans les couleurs `tab10`.

`ascii_earth.py` contient tout ce qui est commun : palette, cadrage, Terre en caractères qui tourne (`HeroGlobe`), lignes et glyphes, rendu vidéo et ligne de commande. Chaque `globe_*.py` hérite de `HeroGlobe` et n'ajoute que ce qu'il dessine autour de la Terre ; `seismes.py` fournit les catalogues de séismes.

```bash
cd illustrations
uv run globe_seismes.py   # ou globe_axes.py, globe_maillage.py, globe_satellites.py, globe_magnetique.py
uv run logo.py
```

Les rendus arrivent dans `illustrations/outputs/` (ignoré par git) ; copier ensuite les `.webm`, `.mov` et `.png` dans `docs/videos/`, et le logo dans `docs/images/logo/`.

Chaque vidéo existe en deux formats, car aucun ne garde la transparence partout : `.webm` (VP9) pour Chrome et Firefox, `.mov` (HEVC) pour Safari. `docs/javascripts/alpha_videos.js` choisit le bon selon le navigateur.

## Déploiement

Chaque push sur `main` reconstruit le site et le publie sur GitHub Pages (`.github/workflows/deploy.yml`). Le workflow peut aussi être relancé à la main depuis l'onglet *Actions*.

**Passage sur un serveur dédié.** Mettre à jour `site_url` dans `mkdocs.yml`, construire avec `uv run mkdocs build --strict`, et copier le contenu de `site/` à la racine du serveur web. Désactiver ensuite GitHub Pages (ou supprimer le dépôt) pour ne pas laisser deux copies en ligne.

**Nom de domaine sur GitHub Pages.** Ajouter un fichier `docs/CNAME` contenant le domaine (par exemple `rt-nuts.fr`), faire pointer le DNS vers GitHub Pages, renseigner le domaine dans les réglages *Pages* du dépôt et mettre `site_url` à jour.

## Licence

Copyright © 2022-2026 NuTS. Tous droits réservés.
