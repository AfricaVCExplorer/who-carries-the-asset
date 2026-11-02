// Generates a 1200x630 gradient share image for every built page into public/og/.
// Run after a build:  npm run build && node scripts/og.mjs && npm run build
import { createRequire } from 'node:module';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
const { chromium } = createRequire(import.meta.url)('playwright');

const font = (f) => `data:font/woff2;base64,${readFileSync(`public/fonts/${f}`).toString('base64')}`;
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const pages = [];
const walk = (dir, rel = '') => {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory() && !['_astro', 'fonts', 'og', 'report'].includes(f)) walk(p, rel ? `${rel}/${f}` : f);
    else if (f === 'index.html') {
      const h = readFileSync(p, 'utf8');
      const title = (h.match(/<meta property="og:title" content="([^"]*)"/) || [])[1] || 'Who carries the asset?';
      pages.push({ file: rel ? rel.replace(/\//g, '-') + '.png' : 'home.png', title: title.replace(/&amp;/g, '&').replace(/&#39;/g, '’'), home: !rel });
    }
  }
};
walk('dist');

const html = (p) => `<!doctype html><html><head><style>
@font-face{font-family:J;font-weight:800;src:url(${font('plus-jakarta-sans-latin-800-normal.woff2')})}
@font-face{font-family:J;font-weight:700;src:url(${font('plus-jakarta-sans-latin-700-normal.woff2')})}
@font-face{font-family:S;font-weight:400;src:url(${font('source-serif-4-latin-400-normal.woff2')})}
body{margin:0;width:1200px;height:630px;background:linear-gradient(110deg,#5B21E6 0%,#C13BDB 55%,#F2766B 100%);color:#fff;position:relative;overflow:hidden}
.c{position:absolute;left:80px;top:72px;width:720px}
.p{display:inline-block;padding:9px 16px;border-radius:99px;background:rgba(255,255,255,.2);font:700 15px/1 J;letter-spacing:.12em;text-transform:uppercase}
h1{margin:34px 0 0;font:800 ${p.home ? 96 : 76}px/1 J;letter-spacing:-.035em}
h1:after{content:'';display:block;width:96px;height:7px;border-radius:7px;background:#fff;margin-top:28px}
p{margin:26px 0 0;font:400 30px/1.3 S;max-width:640px}
svg{position:absolute;right:70px;top:150px;width:330px}
</style></head><body><div class="c"><span class="p">${p.home ? 'A Dream VC capstone project · Investor Accelerator 2026' : 'Who carries the asset?'}</span><h1>${esc(p.home ? 'Who carries the asset?' : p.title)}</h1><p>How African founders use capital as a strategic tool${p.home ? ': nine cases, one framework' : ''}</p></div>
<svg viewBox="0 0 320 300"><path d="M12 46 C 90 42, 190 50, 308 44" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M160 44 C 162 120, 157 210, 161 292" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round"/><rect x="26" y="76" width="112" height="92" rx="4" fill="rgba(255,255,255,.2)" stroke="#fff" stroke-width="2.2"/><rect x="26" y="182" width="112" height="98" rx="4" fill="rgba(255,255,255,.12)" stroke="#fff" stroke-width="2.2"/><rect x="184" y="76" width="112" height="92" rx="4" fill="rgba(255,255,255,.2)" stroke="#fff" stroke-width="2.2"/><rect x="184" y="182" width="112" height="28" rx="4" fill="rgba(255,255,255,.28)" stroke="#fff" stroke-width="2.2"/><rect x="184" y="217" width="112" height="28" rx="4" fill="rgba(255,255,255,.12)" stroke="#fff" stroke-width="2.2"/><rect x="184" y="252" width="112" height="28" rx="4" fill="rgba(255,255,255,.28)" stroke="#fff" stroke-width="2.2"/></svg>
</body></html>`;

const b = await chromium.launch();
const pg = await b.newPage({ viewport: { width: 1200, height: 630 } });
for (const p of pages) { await pg.setContent(html(p)); await pg.waitForTimeout(150); await pg.screenshot({ path: `public/og/${p.file}` }); }
console.log('wrote', pages.length, 'share images');
await b.close();
