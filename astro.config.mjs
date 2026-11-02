import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// GitHub Pages project site: https://cheruiyotnate.github.io/who-carries-the-asset/
// If you move to a custom domain or Netlify/Vercel root, set `base` to '/'.
export default defineConfig({
  site: 'https://cheruiyotnate.github.io',
  base: '/who-carries-the-asset',
  trailingSlash: 'always',
  integrations: [sitemap()],
  build: { inlineStylesheets: 'auto' },
  compressHTML: true,
});
