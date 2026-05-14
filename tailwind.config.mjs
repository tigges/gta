/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Brand palette
        'gta-gold':   '#f59e0b',   // primary amber — GTA identity
        'gta-bright': '#fbbf24',   // brighter amber for large headings
        'gta-teal':   '#0d9488',   // secondary — live / verified states
        'gta-red':    '#ef4444',   // alerts, breaking news
        // Surface system — replaces generic zinc-9xx values
        'surface':    '#0e0e11',   // page background (warm near-black)
        'surface-1':  '#131316',   // card background
        'surface-2':  '#1a1a1e',   // elevated card / hover state
        'border-dim': '#1e1e23',   // subtle borders
        'border-mid': '#2a2a31',   // visible borders, section dividers
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
