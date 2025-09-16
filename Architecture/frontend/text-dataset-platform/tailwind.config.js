/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './public/index.html',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        border: 'rgb(var(--color-border))',
        input: 'rgb(var(--color-input))',
        ring: 'rgb(var(--color-ring))',
        background: 'rgb(var(--color-background))',
        foreground: 'rgb(var(--color-foreground))',
        primary: {
          DEFAULT: 'rgb(var(--color-primary))',
          foreground: 'rgb(var(--color-primary-foreground))',
        },
        secondary: {
          DEFAULT: 'rgb(var(--color-secondary))',
          foreground: 'rgb(var(--color-secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'rgb(var(--color-destructive))',
          foreground: 'rgb(var(--color-destructive-foreground))',
        },
        muted: {
          DEFAULT: 'rgb(var(--color-muted))',
          foreground: 'rgb(var(--color-muted-foreground))',
        },
        accent: {
          DEFAULT: 'rgb(var(--color-accent))',
          foreground: 'rgb(var(--color-accent-foreground))',
        },
        popover: {
          DEFAULT: 'rgb(var(--color-popover))',
          foreground: 'rgb(var(--color-popover-foreground))',
        },
        card: {
          DEFAULT: 'rgb(var(--color-card))',
          foreground: 'rgb(var(--color-card-foreground))',
        },
        success: 'rgb(var(--color-success))',
        warning: 'rgb(var(--color-warning))',
        info: 'rgb(var(--color-info))',
      },
      borderRadius: {
        lg: 'var(--border-radius)',
        md: 'calc(var(--border-radius) - 2px)',
        sm: 'calc(var(--border-radius) - 4px)',
      },
      spacing: {
        'header': 'var(--header-height)',
        'sidebar': 'var(--sidebar-width)',
        'sidebar-collapsed': 'var(--sidebar-collapsed-width)',
      },
      transitionDuration: {
        'fast': '150ms',
        'normal': '300ms',
        'slow': '500ms',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-in-right': 'slideInRight 0.3s ease-in-out',
        'slide-in-left': 'slideInLeft 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-in-out',
        'pulse-slow': 'pulse 2s infinite',
        'bounce-slow': 'bounce 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        'custom-sm': 'var(--shadow-sm)',
        'custom-md': 'var(--shadow-md)',
        'custom-lg': 'var(--shadow-lg)',
        'custom-xl': 'var(--shadow-xl)',
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
        ],
        mono: [
          '"SF Mono"',
          'Monaco',
          '"Inconsolata"',
          '"Roboto Mono"',
          '"Source Code Pro"',
          'monospace',
        ],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
      },
      zIndex: {
        'hide': '-1',
        'auto': 'auto',
        'base': '0',
        'docked': '10',
        'dropdown': '1000',
        'sticky': '1100',
        'banner': '1200',
        'overlay': '1300',
        'modal': '1400',
        'popover': '1500',
        'skipLink': '1600',
        'toast': '1700',
        'tooltip': '1800',
      },
      backdropBlur: {
        xs: '2px',
        sm: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      },
      screens: {
        'xs': '475px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
        // Custom breakpoints
        'mobile': { 'max': '767px' },
        'tablet': { 'min': '768px', 'max': '1023px' },
        'desktop': { 'min': '1024px' },
        // Orientation
        'portrait': { 'raw': '(orientation: portrait)' },
        'landscape': { 'raw': '(orientation: landscape)' },
        // High DPI
        'retina': { 'raw': '(-webkit-min-device-pixel-ratio: 2)' },
      },
      maxWidth: {
        'screen-xs': '475px',
        'screen-sm': '640px',
        'screen-md': '768px',
        'screen-lg': '1024px',
        'screen-xl': '1280px',
        'screen-2xl': '1536px',
      },
      minHeight: {
        'screen-mobile': 'calc(100vh - var(--header-height))',
        'screen-desktop': '100vh',
      },
      gridTemplateColumns: {
        'sidebar': 'var(--sidebar-width) 1fr',
        'sidebar-collapsed': 'var(--sidebar-collapsed-width) 1fr',
        'auto-fit-sm': 'repeat(auto-fit, minmax(200px, 1fr))',
        'auto-fit-md': 'repeat(auto-fit, minmax(250px, 1fr))',
        'auto-fit-lg': 'repeat(auto-fit, minmax(300px, 1fr))',
      },
      aspectRatio: {
        '4/3': '4 / 3',
        '3/2': '3 / 2',
        '2/3': '2 / 3',
        '9/16': '9 / 16',
      },
      cursor: {
        'grab': 'grab',
        'grabbing': 'grabbing',
      },
    },
  },
  plugins: [
    // Custom plugin for component utilities
    function({ addUtilities, addComponents, theme }) {
      const newUtilities = {
        // Glass effect
        '.glass': {
          'background': 'rgba(255, 255, 255, 0.8)',
          'backdrop-filter': 'blur(8px)',
          'border': '1px solid rgba(255, 255, 255, 0.2)',
        },
        '.glass-dark': {
          'background': 'rgba(15, 23, 42, 0.8)',
          'backdrop-filter': 'blur(8px)',
          'border': '1px solid rgba(71, 85, 105, 0.5)',
        },
        // Text truncation utilities
        '.truncate-2': {
          'display': '-webkit-box',
          '-webkit-line-clamp': '2',
          '-webkit-box-orient': 'vertical',
          'overflow': 'hidden',
        },
        '.truncate-3': {
          'display': '-webkit-box',
          '-webkit-line-clamp': '3',
          '-webkit-box-orient': 'vertical',
          'overflow': 'hidden',
        },
        // Scrollbar utilities
        '.scrollbar-thin': {
          'scrollbar-width': 'thin',
        },
        '.scrollbar-none': {
          'scrollbar-width': 'none',
          '&::-webkit-scrollbar': {
            'display': 'none',
          },
        },
        // Layout utilities
        '.full-bleed': {
          'width': '100vw',
          'margin-left': 'calc(-50vw + 50%)',
        },
        '.safe-area-inset': {
          'padding-top': 'env(safe-area-inset-top)',
          'padding-right': 'env(safe-area-inset-right)',
          'padding-bottom': 'env(safe-area-inset-bottom)',
          'padding-left': 'env(safe-area-inset-left)',
        },
      };

      const components = {
        // Button components
        '.btn': {
          'display': 'inline-flex',
          'align-items': 'center',
          'justify-content': 'center',
          'border-radius': theme('borderRadius.md'),
          'font-weight': theme('fontWeight.medium'),
          'font-size': theme('fontSize.sm[0]'),
          'line-height': theme('fontSize.sm[1].lineHeight'),
          'padding': '0.625rem 1rem',
          'height': '2.5rem',
          'transition': 'all 150ms ease-in-out',
          'cursor': 'pointer',
          'border': 'none',
          'outline': 'none',
          '&:focus-visible': {
            'outline': '2px solid rgb(var(--color-ring))',
            'outline-offset': '2px',
          },
          '&:disabled': {
            'opacity': '0.5',
            'cursor': 'not-allowed',
          },
        },
        '.btn-sm': {
          'height': '2rem',
          'padding': '0.5rem 0.75rem',
          'font-size': theme('fontSize.xs[0]'),
          'line-height': theme('fontSize.xs[1].lineHeight'),
        },
        '.btn-lg': {
          'height': '3rem',
          'padding': '0.75rem 1.25rem',
          'font-size': theme('fontSize.lg[0]'),
          'line-height': theme('fontSize.lg[1].lineHeight'),
        },
        // Input components
        '.input': {
          'display': 'flex',
          'width': '100%',
          'border-radius': theme('borderRadius.md'),
          'border': '1px solid rgb(var(--color-border))',
          'background-color': 'transparent',
          'padding': '0.5rem 0.75rem',
          'font-size': theme('fontSize.sm[0]'),
          'line-height': theme('fontSize.sm[1].lineHeight'),
          'transition': 'all 150ms ease-in-out',
          '&:focus': {
            'outline': 'none',
            'ring': '2px solid rgb(var(--color-ring))',
            'border-color': 'transparent',
          },
          '&:disabled': {
            'opacity': '0.5',
            'cursor': 'not-allowed',
          },
          '&::placeholder': {
            'color': 'rgb(var(--color-muted-foreground))',
          },
        },
        // Card component
        '.card': {
          'background-color': 'rgb(var(--color-card))',
          'color': 'rgb(var(--color-card-foreground))',
          'border': '1px solid rgb(var(--color-border))',
          'border-radius': theme('borderRadius.lg'),
          'box-shadow': theme('boxShadow.sm'),
        },
        '.card-header': {
          'padding': theme('spacing.6'),
          'display': 'flex',
          'flex-direction': 'column',
          'gap': theme('spacing.1'),
        },
        '.card-title': {
          'font-size': theme('fontSize.lg[0]'),
          'line-height': theme('fontSize.lg[1].lineHeight'),
          'font-weight': theme('fontWeight.semibold'),
          'letter-spacing': theme('letterSpacing.tight'),
        },
        '.card-description': {
          'font-size': theme('fontSize.sm[0]'),
          'line-height': theme('fontSize.sm[1].lineHeight'),
          'color': 'rgb(var(--color-muted-foreground))',
        },
        '.card-content': {
          'padding': theme('spacing.6'),
          'padding-top': '0',
        },
        '.card-footer': {
          'display': 'flex',
          'align-items': 'center',
          'padding': theme('spacing.6'),
          'padding-top': '0',
        },
        // Badge component
        '.badge': {
          'display': 'inline-flex',
          'align-items': 'center',
          'border-radius': theme('borderRadius.full'),
          'border': '1px solid transparent',
          'padding': '0.125rem 0.375rem',
          'font-size': theme('fontSize.xs[0]'),
          'line-height': theme('fontSize.xs[1].lineHeight'),
          'font-weight': theme('fontWeight.medium'),
          'transition': 'all 150ms ease-in-out',
        },
      };

      addUtilities(newUtilities);
      addComponents(components);
    },
  ],
};