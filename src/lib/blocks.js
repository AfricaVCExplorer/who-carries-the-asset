// Prepare converted blocks for rendering: glossary tooltips in reading order.
export function prepare(blocks, g) {
  let headingSeen = false;
  return blocks.map((b) => {
    if (b.type === 'h') headingSeen = true;
    if (b.type === 'items' && !headingSeen) b = { ...b, hTag: 'h2' };
    if (b.type === 'p') return { ...b, out: b.html ?? g.html(b.text) };
    if (b.type === 'list') return { ...b, out: b.items.map((t) => g.html(t)) };
    if (b.type === 'items') return {
      ...b,
      items: b.items.map((it) => ({ ...it, titleOut: it.title ? g.esc(it.title) : '', out: it.html ?? g.html(it.text) })),
      figure: b.figure ? { ...b.figure, out: g.html(b.figure.caption) } : undefined,
    };
    if (b.type === 'figure') return { ...b, out: g.html(b.caption) };
    return b;
  });
}

export const tocFrom = (blocks) => blocks.filter((b) => b.type === 'h').map((b) => ({ id: b.id, label: b.title }));
