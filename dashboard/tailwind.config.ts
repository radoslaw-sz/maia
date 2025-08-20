import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  safelist: [
    'bg-accent-blue-10',
    'border-accent-blue-30',
    'text-accent-blue',
    'text-text-primary',
    'border-dark-bg'
  ],
  
  theme: {
    extend: {
      colors: {
        'dark-bg': '#0f0f23',
        'card-bg': '#1a1a2e',
        'border-color': '#2a2d47',
        'text-primary': '#e0e6ed',
        'text-secondary': '#9ca3af',
        'accent-blue': {
          DEFAULT: '#64b5f6',                    // Solid accent blue
          10: 'rgba(100,181,246,0.1)',           // 10% opacity
          30: 'rgba(100,181,246,0.3)',           // 30% opacity
        },
        'accent-blue-2': '#42a5f5',
        'accent-blue-3': '#1e88e5',
        'white-10': 'rgba(255, 255, 255, 0.1)',
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace']
      },
      animation: {
        'pulse-slow': 'pulse 2s infinite'
      }
    }
  },
  plugins: [],
}

export default config
