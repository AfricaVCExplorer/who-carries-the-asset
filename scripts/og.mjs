// Generates gradient share images (1200x630) into public/og/.
// Usage: node scripts/og.mjs   (needs Playwright + Chromium)
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { readFileSync } from 'node:fs';
const font = (f) => `data:font/woff2;base64,${readFileSync(`public/fonts/${f}`).toString('base64')}`;
const pages = [
  { file: 'home.png', label: 'A Dream VC capstone project · Investor Accelerator 2026', title: 'Who carries the asset?', sub: 'How African founders use capital as a strategic tool: nine cases, one framework' },
];
const html = (p) => `<!doctype html><html><head><style>
@font-face{font-family:J;font-weight:800;src:url(${font('plus-jakarta-sans-latin-800-normal.woff2')})}
@font-face{font-family:J;font-weight:700;src:url(${font('plus-jakarta-sans-latin-700-normal.woff2')})}
@font-face{font-family:S;font-weight:400;src:url(${font('source-serif-4-latin-400-normal.woff2')})}
body{margin:0;width:1200px;height:630px;background:linear-gradient(110deg,#5B21E6 0%,#C13BDB 55%,#F2766B 100%);color:#fff;position:relative;overflow:hidden}
.c{position:absolute;left:80px;top:72px;width:700px}
.p{display:inline-block;padding:9px 16px;border-radius:99px;background:rgba(255,255,255,.2);font:700 15px/1 J;letter-spacing:.12em;text-transform:uppercase}
h1{margin:34px 0 0;font:800 96px/.98 J;letter-spacing:-.04em}
h1:after{content:'';display:block;width:96px;height:7px;border-radius:7px;background:#fff;margin-top:28px}
p{margin:26px 0 0;font:400 32px/1.3 S;max-width:640px}
svg{position:absolute;right:70px;top:150px;width:330px}
</style></head><body><div class="c"><span class="p">${p.label}</span><h1>${p.title}</h1><p>${p.sub}</p></div>
<svg viewBox="0 0 320 300"><path d="M12 46 C 90 42, 190 50, 308 44" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M160 44 C 162 120, 157 210, 161 292" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round"/><rect x="26" y="76" width="112" height="92" rx="4" fill="rgba(255,255,255,.2)" stroke="#fff" stroke-width="2.2"/><rect x="26" y="182" width="112" height="98" rx="4" fill="rgba(255,255,255,.12)" stroke="#fff" stroke-width="2.2"/><rect x="184" y="76" width="112" height="92" rx="4" fill="rgba(255,255,255,.2)" stroke="#fff" stroke-width="2.2"/><rect x="184" y="182" width="112" height="28" rx="4" fill="rgba(255,255,255,.28)" stroke="#fff" stroke-width="2.2"/><rect x="184" y="217" width="112" height="28" rx="4" fill="rgba(255,255,255,.12)" stroke="#fff" stroke-width="2.2"/><rect x="184" y="252" width="112" height="28" rx="4" fill="rgba(255,255,255,.28)" stroke="#fff" stroke-width="2.2"/></svg>
</body></html>`;
const b = await chromium.launch();
const pg = await b.newPage({ viewport: { width: 1200, height: 630 } });
for (const p of pages) { await pg.setContent(html(p)); await pg.waitForTimeout(300); await pg.screenshot({ path: `public/og/${p.file}` }); console.log('wrote', p.file); }
await b.close();
