import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  output: 'static',
  site: 'https://tigges.github.io',
  base: '/gta',
  integrations: [tailwind()],
});
