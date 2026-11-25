# Cook'd Cafe

An animated cafe website for Sunnybank, Brisbane.

## Deploy to Vercel

Import this repository with the root directory set to the repository root. The included `vercel.json` serves the checked-in `dist/` directory directly. The home page is at `/` and the menu is at `/menu/`. Both pages use local fonts, scripts and artwork.

## Work on the site

Preview the site with `python3 -m http.server 8000 --directory dist`, then open http://localhost:8000. The HTML templates and page generator are in `src/`. After editing templates, run `python3 src/build.py` with `lxml` installed and commit the updated HTML in `dist/`. The styles, browser scripts, fonts and rendered mascot sprites live in `dist/`. Artwork-generation scripts are in `tools/`.
