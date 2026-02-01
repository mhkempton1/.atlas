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
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                display: ['Outfit', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            animation: {
                'slide-in': 'slide-in 0.3s ease-out',
                'spin-slow': 'spin 3s linear infinite',
            },
        },
    },
    plugins: [],
}
