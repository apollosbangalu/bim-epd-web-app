/**
 * Dark Gray Theme Configuration
 * Professional dark theme with gray tones
 */
export const darkGrayTheme = {
  name: 'darkGray',
  colors: {
    bgPrimary: '#1a1a1a',
    bgSecondary: '#2d2d2d',
    bgTertiary: '#3a3a3a',
    textPrimary: '#ffffff',
    textSecondary: '#b0b0b0',
    accentPrimary: '#4a9eff',
    accentSecondary: '#00d4ff',
    border: '#404040',
    shadow: 'rgba(0, 0, 0, 0.5)',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
  },
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
  },
  fontFamily: {
    primary: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: 'Monaco, Courier, monospace',
  },
}

export type Theme = typeof darkGrayTheme