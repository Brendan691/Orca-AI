import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        ocean: {
          50: '#e8f4fd',
          100: '#d0e8fb',
          200: '#a1d2f7',
          300: '#72bbf3',
          400: '#43a5ef',
          500: '#1a73e8',
          600: '#155bb8',
          700: '#10448c',
          800: '#0b2d60',
          900: '#061734',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Noto Sans SC"', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
