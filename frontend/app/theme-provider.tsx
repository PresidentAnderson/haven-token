'use client';

/**
 * Theme Provider
 * Manages light/dark theme switching with system preference support
 */

import * as React from 'react';

type Theme = 'dark' | 'light' | 'system';

type ThemeProviderProps = {
  children: React.ReactNode;
  attribute?: string;
  defaultTheme?: Theme;
  enableSystem?: boolean;
  disableTransitionOnChange?: boolean;
};

type ThemeProviderState = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
};

const ThemeProviderContext = React.createContext<ThemeProviderState | undefined>(
  undefined
);

export function ThemeProvider({
  children,
  attribute = 'class',
  defaultTheme = 'system',
  enableSystem = true,
  disableTransitionOnChange = false,
  ...props
}: ThemeProviderProps) {
  const [theme, setThemeState] = React.useState<Theme>(defaultTheme);
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem('theme') as Theme | null;
    if (stored) {
      setThemeState(stored);
    }
  }, []);

  React.useEffect(() => {
    if (!mounted) return;

    const root = window.document.documentElement;

    if (disableTransitionOnChange) {
      root.classList.add('[&_*]:!transition-none');
    }

    root.classList.remove('light', 'dark');

    if (theme === 'system' && enableSystem) {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')
        .matches
        ? 'dark'
        : 'light';

      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }

    if (disableTransitionOnChange) {
      setTimeout(() => {
        root.classList.remove('[&_*]:!transition-none');
      }, 1);
    }
  }, [theme, enableSystem, disableTransitionOnChange, mounted]);

  const setTheme = React.useCallback((newTheme: Theme) => {
    localStorage.setItem('theme', newTheme);
    setThemeState(newTheme);
  }, []);

  const value = React.useMemo(
    () => ({
      theme,
      setTheme,
    }),
    [theme, setTheme]
  );

  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
}

export const useTheme = () => {
  const context = React.useContext(ThemeProviderContext);

  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
};
