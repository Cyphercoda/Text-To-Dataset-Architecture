/**
 * Theme configuration and utilities
 */

export const themes = {
  light: {
    primary: 'rgb(59 130 246)',
    primaryForeground: 'rgb(255 255 255)',
    secondary: 'rgb(148 163 184)',
    secondaryForeground: 'rgb(15 23 42)',
    muted: 'rgb(248 250 252)',
    mutedForeground: 'rgb(100 116 139)',
    accent: 'rgb(241 245 249)',
    accentForeground: 'rgb(15 23 42)',
    destructive: 'rgb(239 68 68)',
    destructiveForeground: 'rgb(255 255 255)',
    border: 'rgb(226 232 240)',
    input: 'rgb(226 232 240)',
    ring: 'rgb(59 130 246)',
    background: 'rgb(255 255 255)',
    foreground: 'rgb(15 23 42)',
    card: 'rgb(255 255 255)',
    cardForeground: 'rgb(15 23 42)',
    popover: 'rgb(255 255 255)',
    popoverForeground: 'rgb(15 23 42)',
    success: 'rgb(34 197 94)',
    warning: 'rgb(245 158 11)',
    info: 'rgb(59 130 246)',
  },
  dark: {
    primary: 'rgb(59 130 246)',
    primaryForeground: 'rgb(255 255 255)',
    secondary: 'rgb(71 85 105)',
    secondaryForeground: 'rgb(248 250 252)',
    muted: 'rgb(15 23 42)',
    mutedForeground: 'rgb(148 163 184)',
    accent: 'rgb(30 41 59)',
    accentForeground: 'rgb(248 250 252)',
    destructive: 'rgb(239 68 68)',
    destructiveForeground: 'rgb(255 255 255)',
    border: 'rgb(51 65 85)',
    input: 'rgb(51 65 85)',
    ring: 'rgb(59 130 246)',
    background: 'rgb(2 6 23)',
    foreground: 'rgb(248 250 252)',
    card: 'rgb(15 23 42)',
    cardForeground: 'rgb(248 250 252)',
    popover: 'rgb(15 23 42)',
    popoverForeground: 'rgb(248 250 252)',
    success: 'rgb(34 197 94)',
    warning: 'rgb(245 158 11)',
    info: 'rgb(59 130 246)',
  },
} as const;

export type ThemeType = keyof typeof themes;

export const spacing = {
  xs: '0.25rem', // 4px
  sm: '0.5rem',  // 8px
  md: '1rem',    // 16px
  lg: '1.5rem',  // 24px
  xl: '2rem',    // 32px
  '2xl': '3rem', // 48px
  '3xl': '4rem', // 64px
} as const;

export const borderRadius = {
  none: '0',
  sm: '0.25rem',  // 4px
  md: '0.5rem',   // 8px
  lg: '0.75rem',  // 12px
  xl: '1rem',     // 16px
  '2xl': '1.5rem', // 24px
  full: '9999px',
} as const;

export const fontSize = {
  xs: ['0.75rem', { lineHeight: '1rem' }],     // 12px
  sm: ['0.875rem', { lineHeight: '1.25rem' }], // 14px
  base: ['1rem', { lineHeight: '1.5rem' }],    // 16px
  lg: ['1.125rem', { lineHeight: '1.75rem' }], // 18px
  xl: ['1.25rem', { lineHeight: '1.75rem' }],  // 20px
  '2xl': ['1.5rem', { lineHeight: '2rem' }],   // 24px
  '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px
  '4xl': ['2.25rem', { lineHeight: '2.5rem' }],   // 36px
  '5xl': ['3rem', { lineHeight: '1' }],           // 48px
  '6xl': ['3.75rem', { lineHeight: '1' }],        // 60px
} as const;

export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
  none: '0 0 #0000',
} as const;

export const transitions = {
  fast: '150ms ease-in-out',
  normal: '300ms ease-in-out',
  slow: '500ms ease-in-out',
} as const;

export const zIndex = {
  hide: -1,
  auto: 'auto',
  base: 0,
  docked: 10,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800,
} as const;

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

// Component-specific theme tokens
export const components = {
  button: {
    height: {
      sm: '2rem',    // 32px
      md: '2.5rem',  // 40px
      lg: '3rem',    // 48px
    },
    padding: {
      sm: '0.5rem 0.75rem',  // 8px 12px
      md: '0.625rem 1rem',   // 10px 16px
      lg: '0.75rem 1.25rem', // 12px 20px
    },
    fontSize: {
      sm: fontSize.sm,
      md: fontSize.base,
      lg: fontSize.lg,
    },
  },
  input: {
    height: {
      sm: '2rem',    // 32px
      md: '2.5rem',  // 40px
      lg: '3rem',    // 48px
    },
    padding: {
      sm: '0.25rem 0.5rem',   // 4px 8px
      md: '0.5rem 0.75rem',   // 8px 12px
      lg: '0.75rem 1rem',     // 12px 16px
    },
    fontSize: {
      sm: fontSize.sm,
      md: fontSize.base,
      lg: fontSize.lg,
    },
  },
  card: {
    padding: {
      sm: spacing.md,    // 16px
      md: spacing.lg,    // 24px
      lg: spacing.xl,    // 32px
    },
    borderRadius: borderRadius.lg,
    shadow: shadows.md,
  },
  modal: {
    borderRadius: borderRadius.xl,
    shadow: shadows['2xl'],
    backdropBlur: '8px',
  },
  badge: {
    height: {
      sm: '1.25rem', // 20px
      md: '1.5rem',  // 24px
    },
    padding: {
      sm: '0.125rem 0.375rem', // 2px 6px
      md: '0.25rem 0.5rem',    // 4px 8px
    },
    fontSize: {
      sm: fontSize.xs,
      md: fontSize.sm,
    },
    borderRadius: borderRadius.full,
  },
} as const;

// Utility functions for theme management
export class ThemeManager {
  private static instance: ThemeManager;
  private currentTheme: ThemeType = 'light';
  private systemTheme: ThemeType = 'light';

  constructor() {
    if (typeof window !== 'undefined') {
      this.detectSystemTheme();
      this.loadThemeFromStorage();
      this.setupSystemThemeListener();
    }
  }

  static getInstance(): ThemeManager {
    if (!ThemeManager.instance) {
      ThemeManager.instance = new ThemeManager();
    }
    return ThemeManager.instance;
  }

  private detectSystemTheme(): void {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      this.systemTheme = 'dark';
    } else {
      this.systemTheme = 'light';
    }
  }

  private loadThemeFromStorage(): void {
    const savedTheme = localStorage.getItem('theme') as ThemeType;
    if (savedTheme && savedTheme in themes) {
      this.currentTheme = savedTheme;
    } else {
      this.currentTheme = this.systemTheme;
    }
    this.applyTheme(this.currentTheme);
  }

  private setupSystemThemeListener(): void {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      this.systemTheme = e.matches ? 'dark' : 'light';
      if (this.currentTheme === 'system') {
        this.applyTheme(this.systemTheme);
      }
    });
  }

  setTheme(theme: ThemeType | 'system'): void {
    if (theme === 'system') {
      this.currentTheme = this.systemTheme;
      localStorage.setItem('theme', 'system');
    } else {
      this.currentTheme = theme;
      localStorage.setItem('theme', theme);
    }
    this.applyTheme(this.currentTheme);
  }

  getCurrentTheme(): ThemeType {
    return this.currentTheme;
  }

  getSystemTheme(): ThemeType {
    return this.systemTheme;
  }

  private applyTheme(theme: ThemeType): void {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    
    // Update meta theme-color
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', themes[theme].primary);
    }
  }

  toggleTheme(): void {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }
}

// Color utilities
export const getColorValue = (color: string): string => {
  if (color.startsWith('rgb(')) {
    return color;
  }
  return `rgb(${color})`;
};

export const getColorWithOpacity = (color: string, opacity: number): string => {
  const rgbMatch = color.match(/rgb\(([^)]+)\)/);
  if (rgbMatch) {
    return `rgba(${rgbMatch[1]}, ${opacity})`;
  }
  return `rgba(${color}, ${opacity})`;
};

// Animation presets
export const animations = {
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.3 },
  },
  slideInFromRight: {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 },
    transition: { duration: 0.3 },
  },
  slideInFromLeft: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
    transition: { duration: 0.3 },
  },
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 20 },
    transition: { duration: 0.3 },
  },
  scaleIn: {
    initial: { opacity: 0, scale: 0.9 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.9 },
    transition: { duration: 0.2 },
  },
} as const;

// Responsive utilities
export const mediaQueries = {
  sm: `(min-width: ${breakpoints.sm})`,
  md: `(min-width: ${breakpoints.md})`,
  lg: `(min-width: ${breakpoints.lg})`,
  xl: `(min-width: ${breakpoints.xl})`,
  '2xl': `(min-width: ${breakpoints['2xl']})`,
  mobile: `(max-width: ${breakpoints.md})`,
  desktop: `(min-width: ${breakpoints.md})`,
} as const;

// Export theme instance
export const themeManager = typeof window !== 'undefined' ? ThemeManager.getInstance() : null;

export default {
  themes,
  spacing,
  borderRadius,
  fontSize,
  shadows,
  transitions,
  zIndex,
  breakpoints,
  components,
  animations,
  mediaQueries,
  themeManager,
};