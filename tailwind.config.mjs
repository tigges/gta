/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // ── Brand (mapped to CSS vars — change var to update everywhere) ──
        'gta-gold':    'var(--c-brand)',
        'gta-bright':  'var(--c-brand-bright)',
        'gta-teal':    'var(--c-live)',
        'gta-red':     'var(--c-alert)',
        'gta-green':   'var(--c-growth)',    // community, S+, passive income
        'gta-indigo':  'var(--c-economy)',   // economy, capital, complexity
        'gta-reddit':  'var(--c-reddit)',    // Reddit brand colour only

        // ── Surfaces ───────────────────────────────────────────────────────
        'surface':    'var(--c-bg)',
        'surface-deep':'var(--c-bg-deep)',
        'surface-1':  'var(--c-card)',
        'surface-2':  'var(--c-card-raised)',

        // ── Borders ─────────────────────────────────────────────────────────
        'border-dim': 'var(--c-border-1)',
        'border-mid': 'var(--c-border-2)',

        // ── Semantic text tokens (new — use these going forward) ────────────
        //    Replaces raw text-zinc-* values with meaningful names
        'content-0':  'var(--c-text-0)',   // hero headings
        'content-1':  'var(--c-text-1)',   // card titles, primary values
        'content-2':  'var(--c-text-2)',   // strong secondary
        'content-3':  'var(--c-text-3)',   // body text
        'content-4':  'var(--c-text-4)',   // muted labels
        'content-5':  'var(--c-text-5)',   // section labels
        'content-6':  'var(--c-text-6)',   // footnotes
        'content-7':  'var(--c-text-7)',   // watermarks

        // ── Category colors ──────────────────────────────────────────────────
        'cat-franchise':   'var(--c-cat-franchise)',
        'cat-community':   'var(--c-cat-community)',
        'cat-performance': 'var(--c-cat-performance)',
        'cat-economy':     'var(--c-cat-economy)',
        'cat-intel':       'var(--c-cat-intel)',
      },
      fontFamily: {
        sans: ['"Inter"', '"Inter var"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      backgroundImage: {
        'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
};
