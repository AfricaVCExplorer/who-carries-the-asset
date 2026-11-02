"""Check the built site against the PDF source.

1. Every number-like token on the site appears in the PDF text (incl. figure labels).
2. Every PDF paragraph, list item and caption appears on the site.
3. Figures 1-41 are all present with their captions.
Usage: python3 scripts/verify.py <project_dir> <report_txt>
"""
import glob, html, json, re, sys
from bs4 import BeautifulSoup

D, REPORT = sys.argv[1].rstrip('/') + '/', sys.argv[2]
norm = lambda s: re.sub(r'\s+', ' ', s.replace(' ', ' ').replace(' ', ' ')).strip()

# PDF corpus: text dump + all text in the page sources (SVG labels included)
pdf_txt = norm(open(REPORT).read())
order = [f[:-8] for f in json.load(open(D + 'canvas.json'))['order']]
src_text, paras = [], []
for b in order:
    s = BeautifulSoup(open(D + b + '.dc.html').read(), 'html.parser')
    pg = s.select_one('.pg') or s
    src_text.append(norm(pg.get_text(' ')))
    for el in pg.find_all(True):
        if el.name in ('svg', 'style', 'script') or el.find_parent('svg'): continue
        # text blocks: elements with substantial text of their own (not just via children blocks)
        if el.find(['p', 'div', 'li', 'td', 'h1', 'h2', 'h3']) is not None: continue
        t = norm(el.get_text(''))
        if len(t) > 25: paras.append((b, t))
    for cap in pg.select('.cap'):
        paras.append((b, norm(cap.get_text(' ')).split(' ', 2)[-1] if cap.b else norm(cap.get_text(''))))
corpus = pdf_txt + ' ' + ' '.join(src_text)
corpus_nospace = corpus.replace(' ', '')

# Site corpus
site = {}
for f in glob.glob('dist/**/index.html', recursive=True):
    s = BeautifulSoup(open(f).read(), 'html.parser')
    for x in s(['script', 'style', 'noscript']): x.decompose()
    for x in s.select('.gl-tip'): x.decompose()  # glossary definitions checked separately
    main = s.find('main')
    site[f] = norm(main.get_text(' ') if main else '')
site_all = ' '.join(site.values())
site_nospace = site_all.replace(' ', '')

NUM = re.compile(r'(?:[~>≤<]\s?)?(?:US)?[$€£₦]\s?\d[\d,.]*(?:\s?(?:M|B|bn|k|million|billion))?\+?|\b\d[\d,.]*\s?(?:%|M\b|B\b|bn\b|k\b|MWh)\+?|\b\d{1,3}(?:,\d{3})+\+?|\b(?:19|20)\d\d(?:[–-]\d{2,4})?\b|\b\d+(?:\.\d+)?x\b')
problems = []
for f, t in site.items():
    for m in set(NUM.findall(t)):
        tok = m.strip()
        if tok.replace(' ', '') not in corpus_nospace:
            problems.append((f, tok))
print('== 1. Site numbers not found in the PDF:', len(problems))
for f, tok in sorted(problems): print('  ', f.replace('dist/', ''), '|', tok)

missing = [(b, t) for b, t in paras if t.replace(' ', '') not in site_nospace]
print('\n== 2. PDF text blocks not found on the site:', len(missing), 'of', len(paras))
for b, t in missing: print('  ', b, '|', t[:150])

figs = set(int(n) for n in re.findall(r'Figure (\d+)', site_all))
print('\n== 3. Figures present:', len(figs), 'missing:', sorted(set(range(1, 42)) - figs))
