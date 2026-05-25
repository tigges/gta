import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  output: 'static',
  site: 'https://gtavi.ai',
  integrations: [tailwind(), sitemap()],
  vite: {
    build: {
      rollupOptions: {
        output: {
          // Disable automatic code splitting for JS chunks.
          // This bundles each page's JS (including chart component scripts)
          // into a single per-page file rather than shared async chunks.
          // Fixes chart D3 scripts not executing on hub/sub pages because
          // the chart registry and page trigger no longer live in separate bundles.
          manualChunks: undefined,
        },
      },
    },
  },
});
