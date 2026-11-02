# Who carries the asset?

Interactive website for the Dream VC Investor Accelerator 2026 capstone *Who carries the asset? How African founders use capital as a strategic tool: nine cases, one framework* by Princess Oti, Abdullahi Lawal and Nate Cheruiyot.

Live site: https://vcexplorer.github.io/who-carries-the-asset/

The 58-page PDF in `public/report/` is the single source of truth. Every number on the site must match it exactly and carry its source citation.

## Run it locally

Needs Node 20 or later.

```bash
npm install
npm run dev       # http://localhost:4321/who-carries-the-asset/
npm run build     # static site in dist/
npm run preview   # serve the built site
```

## Where the content lives

| What | File |
| --- | --- |
| Title, authors, citation, navigation, acknowledgements | `src/data/site.json` |
| Home page text (research question, findings, framework teaser, Figure 1 caption, closing quote) | `src/data/home.json` |
| Case cards on Home and the cases page (route, region, stage, sector, headline stats with sources) | `src/data/cases.json` |
| Each case page | `src/content/cases/<slug>.json` (M-KOPA is hand-built; the others are generated) |
| Moove comparator | `src/content/moove.json` |
| Sections 00–03, 06–09 | `src/content/sections/<slug>.json` |
| Framework interactives (routes, title test, stage guidance) | `src/content/framework-data.json` |
| Notes on sources, references | `src/content/notes.json`, `src/content/references.json` |
| Glossary (also drives the dotted-underline tooltips) | `src/data/glossary.json` |
| Reading order for previous/next links | `src/data/sequence.json` |
| Colours, type, components, print styles | `src/styles/global.css` |
| Page shell: header, progress bar, footer, citation block | `src/layouts/Base.astro` |

To change a sentence or a number, edit the JSON file and rebuild. Keep the source in brackets next to every figure. A headline stat with an empty `source` is shown without one.

Glossary tooltips are added automatically to the first use of each term on a page (see `src/lib/gloss.js`). Unit-like terms such as M, k and ₦ are skipped.

### Regenerating content from the report source

The case and section JSON files were generated from the report's HTML page sources:

```bash
python3 scripts/web_cases.py <report_html_dir> src/content/cases src/styles/pdf-figs.css
python3 scripts/web_sections.py <report_html_dir> src/content/sections src/styles/pdf-sections.css
```

Figures keep their original markup at the PDF's 682px width; on phones they scroll sideways rather than shrinking. Regenerating overwrites manual edits to those files, though case headline sources are kept.

### Checking the site against the report

```bash
npm run build
python3 scripts/verify.py <report_html_dir> <report_text_dump>
```

This reports any number on the site that does not appear in the PDF, any PDF text block missing from the site, and any missing figure.

## Share images

`npm run build && node scripts/og.mjs && npm run build` regenerates a 1200×630 gradient share image for every page in `public/og/` (needs Playwright with Chromium).

## Deployment

### GitHub Pages (current)

1. In the repo, go to **Settings → Pages** and set **Source** to **GitHub Actions**.
2. Push to `main`. The workflow in `.github/workflows/deploy.yml` builds and publishes the site.

The site lives under `/who-carries-the-asset/`, which is set as `base` in `astro.config.mjs`.

### Netlify or Vercel

Import the repo, use build command `npm run build` and output folder `dist`. In `astro.config.mjs`, set `base: '/'` and change `site` to the new address.

## Accessibility

- White text sits only on the violet part of the gradient. On narrow screens the hero switches to a violet band, with the full gradient kept as a thin rule.
- All interactive parts work with a keyboard. Filters use `aria-pressed`, and result counts are announced.
- Without JavaScript, all content is still shown.
- Motion is switched off when the reader's system asks for reduced motion.
