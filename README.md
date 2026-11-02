# Who carries the asset?

Interactive website for the Dream VC Investor Accelerator 2026 capstone *Who carries the asset? How African founders use capital as a strategic tool: nine cases, one framework* by Princess Oti, Abdullahi Lawal and Nate Cheruiyot.

Live site: https://cheruiyotnate.github.io/who-carries-the-asset/

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
| Home page text (research question, findings, framework teaser, Figure 1 caption) | `src/data/home.json` |
| Case cards: route, region, stage, sector, headline stats and their sources | `src/data/cases.json` |
| Glossary (also drives the dotted-underline tooltips) | `src/data/glossary.json` |
| Colours, type, components, print styles | `src/styles/global.css` |
| Page shell: header, progress bar, footer, citation block | `src/layouts/Base.astro` |

To change a sentence or a number, edit the JSON file and rebuild. Keep the source in brackets next to every figure.

Glossary tooltips are added automatically to the first use of each term on a page (see `src/lib/gloss.js`). Unit-like terms such as M, k and ₦ are skipped.

## Share images

`node scripts/og.mjs` regenerates the 1200×630 gradient images in `public/og/` (needs Playwright with Chromium).

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
