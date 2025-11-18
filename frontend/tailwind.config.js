/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}', '../**/*.py'],
  theme: {
    extend: {
      colors: {
        // 统一的深色主题配色方案
        surface: {
          DEFAULT: '#1a1a1a',
          elevated: '#242424',
          hover: '#2a2a2a',
        },
        border: {
          DEFAULT: '#333333',
          light: '#404040',
          dark: '#262626',
        },
        primary: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
          active: '#1d4ed8',
          light: '#60a5fa',
        },
        success: {
          DEFAULT: '#10b981',
          hover: '#059669',
        },
        danger: {
          DEFAULT: '#ef4444',
          hover: '#dc2626',
        },
        warning: {
          DEFAULT: '#f59e0b',
          hover: '#d97706',
        },
        text: {
          primary: '#ffffff',
          secondary: '#a3a3a3',
          tertiary: '#737373',
          disabled: '#525252',
        },
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(0, 0, 0, 0.15)',
        'medium': '0 4px 16px rgba(0, 0, 0, 0.2)',
        'large': '0 8px 24px rgba(0, 0, 0, 0.25)',
      },
      transitionDuration: {
        '200': '200ms',
        '300': '300ms',
      },
    }
  },
  plugins: []
};
