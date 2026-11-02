// Prefix internal links with the configured base path.
export const base = import.meta.env.BASE_URL.replace(/\/?$/, '/');
export const u = (path = '') => base + String(path).replace(/^\//, '');
