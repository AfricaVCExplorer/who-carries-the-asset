"""Convert the PDF case pages (dc.html sources) into site JSON for the case template.

Usage: python3 web_cases.py <project_dir> <out_dir>
Text is taken verbatim from the PDF source; figures that are not timelines are kept
as their original markup (rendered at the PDF's 682px width) with any page-level
classes they rely on scoped into src/styles/pdf-figs.css.
"""
import json, re, sys
from bs4 import BeautifulSoup, NavigableString, Tag

D, OUT = sys.argv[1].rstrip('/') + '/', sys.argv[2].rstrip('/') + '/'
CSS_OUT = sys.argv[3] if len(sys.argv) > 3 else None

CASES = [
    # slug, order, number, pages(boards), pdf pages, section, sectionTitle, route, illustration
    ('mnt-halan', 2, '2', ['P15', 'P16', 'P17'], [18, 20], '04', 'Case studies: East & North Africa', 'debt'),
    ('nala', 3, '3', ['P18', 'P19', 'P19b'], [21, 23], '04', 'Case studies: East & North Africa', 'noasset'),
    ('sendy', 4, '4', ['P20', 'P21', 'P21b'], [24, 26], '04', 'Case studies: East & North Africa', 'assetequity'),
    ('moniepoint', 5, '5', ['P23', 'P24'], [28, 29], '05', 'Case studies: West Africa', 'deposits'),
    ('autogirl', 6, '6', ['P25', 'P26', 'P27'], [30, 32], '05', 'Case studies: West Africa', 'partner'),
    ('feegor', 7, '7', ['P29', 'P30', 'P31'], [34, 36], '05', 'Case studies: West Africa', 'partner'),
    ('earthbond', 8, '8', ['P32', 'P33'], [37, 38], '05', 'Case studies: West Africa', 'partner'),
    ('lemfi', 9, '9', ['P34', 'P35'], [39, 40], '05', 'Case studies: West Africa', 'noasset'),
]

CHIP = {'eq': 'Equity', 'dt': 'Debt', 'gr': 'Grant', 'rv': 'Revenue'}
used_classes = {}


def txt(el):
    s = el.get_text('') if isinstance(el, Tag) else str(el)
    return re.sub(r'\s+', ' ', s).strip()


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:48]


def clean_svg_ids(html, board):
    # make pattern/marker ids unique per board to avoid clashes on one page
    ids = set(re.findall(r'id="([^"]+)"', html))
    for i in ids:
        html = html.replace(f'id="{i}"', f'id="{board}-{i}"').replace(f'url(#{i})', f'url(#{board}-{i})')
    return html


def figure_block(div, board):
    cap = div.select_one('.cap')
    num = int(re.search(r'\d+', cap.b.get_text()).group())
    caption = txt(cap.find('span')) if cap.find('span') else txt(cap)[len(cap.b.get_text()):].strip()
    ft = div.find('div', class_='ft', recursive=False)
    title = txt(ft) if ft else None
    if ft: ft.decompose()
    cap.decompose()
    for el in div.find_all(True):
        for c in el.get('class', []):
            used_classes.setdefault(board, set()).add(c)
    inner = ''.join(str(c) for c in div.contents).strip()
    # keep the wrapper's own layout (height, position) but not its outer margins
    style = re.sub(r'margin[^;]*;?', '', div.get('style', '')).strip()
    if style:
        inner = f'<div style="{style}">{inner}</div>'
    # aria-label of the main svg serves as the text alternative
    svg = div.find('svg', attrs={'role': 'img'})
    alt = svg.get('aria-label') if svg else None
    return {'type': 'raw', 'number': num, 'title': title, 'html': clean_svg_ids(inner, board), 'board': board,
            'caption': caption, 'alt': alt}


def is_quote(div):
    t = txt(div)
    return t.startswith('“') and not div.select_one('.cap')


def convert(case):
    slug, order, number, boards, pdfp, sec, sect, route = case
    data = {'slug': slug, 'order': order, 'number': number, 'section': sec, 'sectionTitle': sect,
            'pdfPages': pdfp, 'blocks': [], 'why': [], 'lessons': []}
    first = BeautifulSoup(open(D + boards[0] + '.dc.html').read(), 'html.parser').select_one('.pg')
    # header
    h1 = first.find('h1')
    head = h1.parent
    data['name'] = txt(h1)
    pill = head.select_one('.pill')
    data['pill'] = txt(pill)
    data['country'] = txt(pill).split('·', 1)[1].strip()
    fdiv = h1.find_next_sibling('div')
    data['founders'] = txt(fdiv)
    data['heroStats'] = [{'value': txt(st.b), 'label': txt(st)[len(txt(st.b)):].strip(), 'source': ''} for st in head.select('.st')]
    art = None
    for sv in first.find_all('svg', recursive=False):
        art = sv
    if art is None:
        art = head.find_next_sibling('svg')
    if art is not None:
        a = BeautifulSoup(str(art), 'html.parser').svg
        for k in ('style', 'width', 'height'):
            if k in a.attrs: del a[k]
        a['class'] = 'case-art'; a['aria-hidden'] = 'true'; a['focusable'] = 'false'
        data['art'] = clean_svg_ids(str(a), boards[0] + 'art')
    mode = None
    for b in boards:
        pg = BeautifulSoup(open(D + b + '.dc.html').read(), 'html.parser').select_one('.pg')
        bd = pg.select_one('.bd')
        for ch in bd.find_all(recursive=False):
            cls = ch.get('class', [])
            if 'ks' in cls:
                f = {}
                for d in ch.find_all('div', recursive=False):
                    lb = d.select_one('.lb'); key = txt(lb); lb.extract()
                    if key == 'Status':
                        sv = d.find('svg'); data['statusIcon'] = str(sv) if sv else ''
                        if sv: sv.extract()
                    f[key] = txt(d)
                data['facts'] = {'business': f.get('Business'), 'investors': f.get('Main investors'), 'route': route,
                                 'routeText': f.get('Who carries the asset'), 'status': f.get('Status')}
            elif ch.name == 'h3':
                t = txt(ch)
                if t.startswith('Why this'):
                    data['whyTitle'] = t; mode = 'why'
                else:
                    mode = 'analysis'
                    if ':' in t:
                        a, s = t.split(':', 1)
                        data['blocks'].append({'type': 'h', 'id': slugify(a), 'title': a.strip(), 'sub': s.strip()})
                    else:
                        data['blocks'].append({'type': 'h', 'id': slugify(t), 'title': t})
            elif ch.name == 'p':
                lead = ch.find('b', class_='h')
                if mode == 'why':
                    data['why'].append(txt(ch))
                elif lead is not None:
                    lt = txt(lead); lead.extract()
                    data['blocks'].append({'type': 'p', 'lead': lt, 'id': slugify(lt.rstrip('.')), 'text': txt(ch)})
                else:
                    data['blocks'].append({'type': 'p', 'text': txt(ch)})
            elif 'lb' in cls:
                data['analysisLabel'] = txt(ch); mode = 'analysis'
            elif ch.select_one('.tl'):
                tl = ch.select_one('.tl')
                entries = []
                for tr in tl.select('.tr'):
                    d = txt(tr.select_one('.d'))
                    k = tr.select_one('.k'); key = None
                    if k and k.get('style'):
                        m = re.search(r'background:(#[0-9A-Fa-f]{6})', k['style'])
                        key = m.group(1).upper() if m else None
                    ins, insc = [], []
                    for c in tr.select('.c'):
                        ins.append(txt(c)); insc.append([x for x in c.get('class', []) if x != 'c'][0])
                    for el in tr.select('.d, .k, .c'): el.extract()
                    e = {'date': d, 'instruments': ins, 'cls': insc, 'text': txt(tr)}
                    if key: e['key'] = key
                    entries.append(e)
                cap = ch.select_one('.cap')
                data['journey'] = {'title': txt(ch.select_one('.ft')), 'entries': entries,
                                   'figure': {'number': int(re.search(r'\d+', cap.b.get_text()).group()), 'caption': txt(cap.find('span'))}}
                mode = 'journey'
            elif ch.select('.dm'):
                mode = 'analysis'
                data['blocks'].append({'type': 'dims', 'items': [
                    {'id': slugify(txt(dm.select_one('.h'))), 'title': txt(dm.select_one('.h')), 'text': txt(dm.select_one('.b'))}
                    for dm in ch.select('.dm')]})
            elif ch.select_one('.cap'):
                fb = figure_block(ch, b)
                if mode == 'why' and 'journey' not in data:
                    data['journey'] = {'title': fb.pop('title'), 'raw': fb, 'entries': [],
                                       'figure': {'number': fb['number'], 'caption': fb['caption']}}
                    mode = 'journey'
                else:
                    data['blocks'].append(fb)
            elif ch.select_one('.lb') and 'dashed' in ch.get('style', ''):
                lb = ch.select_one('.lb'); label = txt(lb); lb.extract()
                data['blocks'].append({'type': 'callout', 'label': label, 'text': txt(ch)})
            elif 'kl' in cls:
                for li in ch.select('ol > li'):
                    if li.i: li.i.extract()
                    data['lessons'].append(txt(li))
            elif is_quote(ch):
                q = [d for d in ch.find_all('div') if 'italic' in d.get('style', '') or 'q' in d.get('class', [])]
                data['quote'] = txt(q[0]) if q else txt(ch).lstrip('“').strip()
            else:
                print('UNHANDLED', slug, b, ch.name, cls, txt(ch)[:80], file=sys.stderr)
    data.setdefault('analysisLabel', 'Analysis across framework dimensions')
    return data


css_rules = []
for case in CASES:
    d = convert(case)
    try:
        prev = json.load(open(OUT + d['slug'] + '.json'))
        src = {s['value']: s.get('source', '') for s in prev.get('heroStats', [])}
        for s in d['heroStats']: s['source'] = src.get(s['value'], '')
        for k in ('description',):
            if k in prev: d[k] = prev[k]
    except FileNotFoundError:
        pass
    json.dump(d, open(OUT + d['slug'] + '.json', 'w'), ensure_ascii=False, indent=2)
    print(d['slug'], len(d['blocks']), 'blocks', len(d['journey']['entries']), 'journey', len(d['lessons']), 'lessons',
          'quote' if d.get('quote') else 'NOQUOTE', [s['value'] + ' ' + s['label'] for s in d['heroStats']])

# Scope page-level classes used inside raw figures
SKIP = {'cap'}
for b, classes in used_classes.items():
    t = open(D + b + '.dc.html').read()
    style = t[t.index('<style>') + 7:t.index('</style>')]
    for rule in re.findall(r'([^{}]+)\{([^{}]*)\}', style):
        sel, body = rule[0].strip(), rule[1]
        if sel.startswith('@'): continue
        sels = [s.strip() for s in sel.split(',')]
        keep = [s for s in sels if any(re.search(r'\.' + re.escape(c) + r'\b', s) for c in classes - SKIP)]
        if keep:
            css_rules.append(','.join(f'.pf-{b} {s}' for s in keep) + '{' + body + '}')
if CSS_OUT:
    open(CSS_OUT, 'w').write('/* Generated by web_cases.py: page-level classes used inside PDF figures, scoped per page. */\n' + '\n'.join(css_rules) + '\n')
    print(len(css_rules), 'scoped css rules')
