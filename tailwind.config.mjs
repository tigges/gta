/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // ── Functional accents (site-wide) ────────────────────────────────
        'gta-gold':    'var(--c-brand)',
        'gta-bright':  'var(--c-brand-bright)',
        'gta-teal':    'var(--c-live)',
        'gta-red':     'var(--c-alert)',
        'gta-green':   'var(--c-growth)',
        'gta-indigo':  'var(--c-economy)',
        'gta-reddit':  'var(--c-reddit)',

        // ── Title identity (3 places only: nav dot · section dot · border-left)
        'gta-vi-coral':    'var(--c-title-vi)',
        'gta-vi-alt':      'var(--c-title-vi-alt)',
        'gta-online-vivid':'var(--c-title-online)',
        'gta-sa-red':      'var(--c-title-sa)',
        'gta-vc-pink':     'var(--c-title-vc)',

        // ── Page identity resolver (inherits from data-title-context) ──────
        'identity':    'var(--c-identity)',

        // ── Surfaces ──────────────────────────────────────────────────────
        'surface':     'var(--c-bg)',
        'surface-deep':'var(--c-bg-deep)',
        'surface-1':   'var(--c-card)',
        'surface-2':   'var(--c-card-raised)',

        // ── Borders ───────────────────────────────────────────────────────
        'border-dim':  'var(--c-border-1)',
        'border-mid':  'var(--c-border-2)',

        // ── Text tokens ───────────────────────────────────────────────────
        'content-0':   'var(--c-text-0)',
        'content-1':   'var(--c-text-1)',
        'content-2':   'var(--c-text-2)',
        'content-3':   'var(--c-text-3)',
        'content-4':   'var(--c-text-4)',
        'content-5':   'var(--c-text-5)',
        'content-6':   'var(--c-text-6)',
        'content-7':   'var(--c-text-7)',

        // ── Neutral label / badge ─────────────────────────────────────────
        'badge-text':   'var(--c-badge-text)',
        'badge-border': 'var(--c-badge-border)',

        // ── Category colours ──────────────────────────────────────────────
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
