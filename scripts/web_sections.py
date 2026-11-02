"""Convert the PDF's prose sections (dc.html sources) into site JSON.

Usage: python3 scripts/web_sections.py <project_dir> <out_dir> <css_out>

Text is copied verbatim. Numbered lists become structured items; figures and tables
keep their original markup (scoped page CSS goes to css_out).
"""
import json, re, sys
from bs4 import BeautifulSoup, Tag

D, OUT, CSS_OUT = sys.argv[1].rstrip('/') + '/', sys.argv[2].rstrip('/') + '/', sys.argv[3]

SECTIONS = [
    ('introduction', ['P03', 'P04'], [3, 4]),
    ('executive-summary', ['P05', 'P06', 'P06b'], [5, 7]),
    ('methodology', ['P07', 'P08', 'P08b', 'P09'], [8, 11]),
    ('literature-review', ['P10', 'P11'], [12, 13]),
    ('cases-east', ['P12'], [14, 14]),
    ('cases-west', ['P22'], [27, 27]),
    ('synthesis', ['P36', 'P36b', 'P37', 'P37b', 'P38', 'P39'], [41, 46]),
    ('framework', ['P40', 'P41', 'P42'], [47, 49]),
    ('implications', ['P43'], [50, 50]),
    ('conclusion', ['P44', 'P45'], [51, 52]),
]

used = {}


def txt(el):
    s = el.get_text('') if isinstance(el, Tag) else str(el)
    return re.sub(r'\s+', ' ', s).strip()


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:56]


def note_classes(el, board):
    for e in [el] + el.find_all(True):
        for c in e.get('class', []) or []:
            used.setdefault(board, set()).add(c)


def uniq_ids(html, board):
    for i in set(re.findall(r'id="([^"]+)"', html)):
        html = html.replace(f'id="{i}"', f'id="{board}-{i}"').replace(f'url(#{i})', f'url(#{board}-{i})').replace(f'href="#{i}"', f'href="#{board}-{i}"')
    return html


def inline_html(el):
    """Paragraph HTML keeping only <b>/<i> emphasis; nowrap spans become plain text (re-added by gloss)."""
    out = []
    for c in el.children:
        if isinstance(c, Tag):
            if c.name in ('b', 'strong'):
                out.append(f'<b>{esc(txt(c))}</b>')
            elif c.name in ('i', 'em'):
                out.append(f'<i>{esc(txt(c))}</i>')
            else:
                out.append(esc(c.get_text('')))
        else:
            out.append(esc(str(c)))
    return re.sub(r'\s+', ' ', ''.join(out)).strip()


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def number_child(el):
    for c in el.find_all(['div', 'span', 'i'], recursive=False):
        if re.fullmatch(r'\d{1,2}', txt(c)):
            return c
    return None


def find_items(container):
    """Numbered cards/rows: an element with a direct child that holds just a number."""
    items = []
    for el in container.find_all(['div', 'li']):
        n = number_child(el)
        if n is None or el.find_parent(lambda t: t in [i['_el'] for i in items]):
            continue
        rest = [c for c in el.find_all(True, recursive=False) if c is not n]
        # flatten one wrapper level
        if len(rest) == 1 and rest[0].name == 'div' and len(rest[0].find_all(True, recursive=False)) >= 1 and rest[0].find('p') is None and not rest[0].get('class'):
            rest = rest[0].find_all(True, recursive=False)
        rest = [r for r in rest if 'tp' not in (r.get('class') or [])]
        accent = None
        tp = el.find(class_='tp')
        m = re.search(r'background:(#[0-9A-Fa-f]{6})', (tp.get('style', '') if tp else '') or '') or re.search(r'border-left:\d+px solid (#[0-9A-Fa-f]{6})', el.get('style', ''))
        if m: accent = m.group(1)
        if len(rest) >= 2:
            item = {'n': txt(n), 'title': txt(rest[0]), 'text': ' '.join(txt(r) for r in rest[1:])}
        elif len(rest) == 1:
            item = {'n': txt(n), 'html': inline_html(rest[0]) if rest[0].name == 'p' else esc(txt(rest[0]))}
        else:
            continue
        if accent: item['accent'] = accent
        item['_el'] = el
        items.append(item)
    for i in items: i.pop('_el')
    return items


def is_quote(div):
    return txt(div).startswith('“') or 'pq' in (div.get('class') or [])


def quote_text(div):
    for d in div.find_all('div'):
        if 'italic' in d.get('style', '') or 'q' in (d.get('class') or []):
            return txt(d)
    return txt(div).lstrip('“').strip()


def opener(bd, board):
    first = bd.find(recursive=False)
    h1 = first.find('h1') if first else None
    if not h1:
        return None, None
    for s in h1.find_all('span'): s.extract()
    pill = first.find('span')
    big = [d for d in first.find_all('div') if re.fullmatch(r'\d\d', txt(d))]
    art = first.find('svg')
    a = None
    if art is not None:
        a = BeautifulSoup(str(art), 'html.parser').svg
        for k in ('style', 'width', 'height'):
            if k in a.attrs: del a[k]
        a['class'] = 'sec-art'; a['aria-hidden'] = 'true'; a['focusable'] = 'false'
        a = uniq_ids(str(a), board + 'art')
    info = {'title': txt(h1), 'pill': txt(pill) if pill else None, 'number': txt(big[0]) if big else None, 'art': a}
    first.extract()
    return info, first


def convert(slug, boards, pdfp):
    data = {'slug': slug, 'pdfPages': pdfp, 'blocks': []}
    B = data['blocks']
    pending = []  # raw pieces awaiting a sibling caption

    def flush_pending():
        for raw, board in pending:
            B.append({'type': 'flow', 'html': raw, 'board': board})
        pending.clear()

    for bi, b in enumerate(boards):
        pg = BeautifulSoup(open(D + b + '.dc.html').read(), 'html.parser').select_one('.pg')
        bd = pg.select_one('.bd')
        flush_pending()  # figure groups never span pages
        if bi == 0:
            info, _ = opener(bd, b)
            if info: data.update(info)
        for ch in bd.find_all(recursive=False):
            cls = ch.get('class') or []
            note_classes(ch, b)
            if ch.name in ('h2', 'h3'):
                flush_pending()
                B.append({'type': 'h', 'id': slugify(txt(ch)), 'title': txt(ch), 'level': 2 if ch.name == 'h2' else 3})
            elif ch.name == 'p':
                flush_pending()
                blk = {'type': 'p', 'text': txt(ch)}
                if ch.find(['b', 'i', 'strong', 'em']): blk = {'type': 'p', 'html': inline_html(ch)}
                if 'lead' in cls: blk['lead'] = True
                B.append(blk)
            elif ch.name == 'ul':
                flush_pending()
                B.append({'type': 'list', 'items': [txt(li) for li in ch.find_all('li')]})
            elif 'lb' in cls:
                flush_pending()
                B.append({'type': 'label', 'text': txt(ch)})
            elif 'cap' in cls:
                # caption for the preceding sibling pieces
                num = int(re.search(r'\d+', ch.b.get_text()).group())
                cap = txt(ch.find('span')) if ch.find('span') else txt(ch)[len(ch.b.get_text()):].strip()
                title = None
                html = ''.join(p for p, _ in pending)
                pending.clear()
                m = re.match(r'\s*<div class="ft">(.*?)</div>', html, re.S)
                if m:
                    title = txt(BeautifulSoup(m.group(1), 'html.parser')); html = html[m.end():]
                if not html.strip() and B and B[-1]['type'] == 'items':
                    B[-1]['figure'] = {'number': num, 'caption': cap}
                    continue
                B.append({'type': 'figure', 'number': num, 'title': title, 'html': uniq_ids(html, b), 'board': b, 'caption': cap})
            elif ch.select_one('.cap') and not is_quote(ch):
                flush_pending()
                cap = ch.select_one('.cap')
                num = int(re.search(r'\d+', cap.b.get_text()).group())
                capt = txt(cap.find('span')) if cap.find('span') else txt(cap)[len(cap.b.get_text()):].strip()
                ft = ch.find('div', class_='ft', recursive=False)
                title = txt(ft) if ft else None
                if ft: ft.decompose()
                cap.decompose()
                inner = ''.join(str(c) for c in ch.contents).strip()
                style = re.sub(r'margin[^;]*;?', '', ch.get('style', '')).strip()
                if style: inner = f'<div style="{style}">{inner}</div>'
                svg = ch.find('svg', attrs={'role': 'img'})
                B.append({'type': 'figure', 'number': num, 'title': title, 'html': uniq_ids(inner, b), 'board': b,
                          'caption': capt, 'alt': svg.get('aria-label') if svg else None})
            elif is_quote(ch):
                flush_pending()
                B.append({'type': 'quote', 'text': quote_text(ch)})
            else:
                items = find_items(ch)
                seq_ok = [i['n'] for i in items] == [str(k) for k in range(int(items[0]['n']), int(items[0]['n']) + len(items))] if items else False
                if len(items) >= 2 and seq_ok and not ch.find('table'):
                    flush_pending()
                    B.append({'type': 'items', 'items': items})
                else:
                    pending.append((str(ch), b))
        # a page break does not end a figure group only if a caption follows; otherwise flush
    flush_pending()
    return data


for slug, boards, pdfp in SECTIONS:
    d = convert(slug, boards, pdfp)
    json.dump(d, open(OUT + slug + '.json', 'w'), ensure_ascii=False, indent=2)
    print(slug, d.get('number'), d.get('title'), '|', ' '.join(b['type'] + (str(b.get('number', '')) if b['type'] == 'figure' else '') for b in d['blocks']))

rules = []
for b, classes in used.items():
    t = open(D + b + '.dc.html').read()
    style = t[t.index('<style>') + 7:t.index('</style>')]
    for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', style):
        sel = sel.strip()
        if sel.startswith('@'): continue
        keep = [s.strip() for s in sel.split(',') if any(re.search(r'\.' + re.escape(c) + r'(?![\w-])', s) for c in classes - {'cap', 'pg', 'bd', 'rh', 'rf', 'lead'})]
        if keep:
            rules.append(','.join(f'.pf-{b} {s}' for s in keep) + '{' + body + '}')
open(CSS_OUT, 'w').write('/* Generated by web_sections.py: page-level classes used in PDF figures and tables, scoped per page. */\n' + '\n'.join(rules) + '\n')
print(len(rules), 'scoped rules')
