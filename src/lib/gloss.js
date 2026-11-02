// Glossary tooltips: marks the FIRST occurrence of each glossary term on a page.
// Usage in a page's frontmatter:  const g = makeGloss();  g.html("some text")
// Call g.html() on strings in reading order so "first occurrence" is accurate.
import glossary from '../data/glossary.json';

// Unit-like or self-evident terms are not marked.
const SKIP = new Set(['k', 'M', 'B / bn', '₦', 'US / USD', 'UK', 'EU', 'UAE', 'CEO', 'COO', 'MBA', 'HBS', 'COVID-19', 'SUV', 'PE', 'LP']);

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const reEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const entries = glossary.terms
  .filter((t) => !SKIP.has(t.term))
  .map((t) => {
    const isPhrase = /[a-z]/.test(t.term) && !/^[A-Z][a-z]?[A-Z]/.test(t.term) && t.term !== 'SaaS' && t.term !== 'KfW';
    // Phrases (e.g. "Platform capital") match case-insensitively; acronyms match exactly.
    return { ...t, re: new RegExp(`(?<![\\w-])${reEsc(t.term)}(?![\\w-])`, isPhrase ? 'i' : '') };
  })
  .sort((a, b) => b.term.length - a.term.length);

let counter = 0;

export function makeGloss() {
  const seen = new Set();
  function html(text) {
    if (!text) return '';
    // Find the earliest unseen match repeatedly, building output left to right.
    let out = '';
    let rest = text;
    for (;;) {
      let best = null;
      for (const e of entries) {
        if (seen.has(e.term)) continue;
        const m = e.re.exec(rest);
        if (m && (!best || m.index < best.m.index || (m.index === best.m.index && m[0].length > best.m[0].length))) best = { e, m };
      }
      if (!best) break;
      const { e, m } = best;
      seen.add(e.term);
      const id = `gl-${++counter}`;
      out += esc(rest.slice(0, m.index));
      out += `<span class="gl"><button type="button" class="gl-t" aria-describedby="${id}">${esc(m[0])}</button><span role="tooltip" id="${id}" class="gl-tip"><b>${esc(e.term)}</b> ${esc(e.definition)}</span></span>`;
      rest = rest.slice(m.index + m[0].length);
    }
    return out + esc(rest);
  }
  return { html, esc };
}

export { esc };
