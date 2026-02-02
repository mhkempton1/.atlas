/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: {
                    DEFAULT: 'var(--bg-app)',
                    dark: '#020617',
                },
                surface: {
                    DEFAULT: 'var(--bg-card)',
                    hover: 'var(--bg-card-hover)',
                    dark: '#0f172a',
                },
                primary: {
                    DEFAULT: 'var(--primary)',
                    dim: 'var(--primary-dim)',
                    glow: 'var(--primary-glow)',
                },
                secondary: 'var(--secondary)',
                text: {
                    main: 'var(--text-main)',
                    muted: 'var(--text-muted)',
                    bright: 'var(--text-bright)',
                },
                border: 'var(--border)',
                neon: {
                    cyan: '#00f2ff',
                    lime: '#39ff14',
                    amber: '#ffb100',
                },
                space: {
                    blue: '#1a2a6c',
                    orange: '#f2994a',
                    white: '#ffffff',
                },
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                display: ['Outfit', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            animation: {
                'slide-in': 'slide-in 0.3s ease-out',
                'spin-slow': 'spin 3s linear infinite',
                'flicker': 'flicker 0.15s infinite',
                'scanline': 'scanline 8s linear infinite',
                'pulse-neon': 'pulse-neon 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'space-flow': 'space-flow 15s linear infinite',
            },
            keyframes: {
                flicker: {
                    '0%, 100%': { opacity: '0.97' },
                    '50%': { opacity: '1' },
                },
                scanline: {
                    '0%': { transform: 'translateY(-100%)' },
                    '100%': { transform: 'translateY(100%)' },
                },
                'pulse-neon': {
                    '0%, 100%': { opacity: '1', filter: 'brightness(1)' },
                    '50%': { opacity: '0.8', filter: 'brightness(1.5)' },
                },
                'space-flow': {
                    '0%': { 'background-position': '0% 50%' },
                    '50%': { 'background-position': '100% 50%' },
                    '100%': { 'background-position': '0% 50%' },
                },
            },
        },
    },
    plugins: [],
}
