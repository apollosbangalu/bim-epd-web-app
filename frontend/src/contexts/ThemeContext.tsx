/**
 * Theme Context
 * Provides theme switching functionality throughout the app
 */
import React, { createContext, useContext, useState, useEffect } from 'react'
import { Theme } from '../styles/themes/darkGray'
import { darkGrayTheme } from '../styles/themes/darkGray'
import { darkNavyTheme } from '../styles/themes/darkNavy'

interface ThemeContextType {
  theme: Theme
  themeName: 'darkGray' | 'darkNavy'
  setTheme: (themeName: 'darkGray' | 'darkNavy') => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [themeName, setThemeName] = useState<'darkGray' | 'darkNavy'>(() => {
    // Load theme from localStorage or default to darkGray
    const saved = localStorage.getItem('theme')
    return (saved === 'darkNavy' ? 'darkNavy' : 'darkGray') as 'darkGray' | 'darkNavy'
  })

  const theme = themeName === 'darkNavy' ? darkNavyTheme : darkGrayTheme

  const setTheme = (newTheme: 'darkGray' | 'darkNavy') => {
    setThemeName(newTheme)
    localStorage.setItem('theme', newTheme)
  }

  // Apply theme to document root
  useEffect(() => {
    const root = document.documentElement
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value)
    })
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, themeName, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}