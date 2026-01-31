import React from 'react'
import { useTheme } from '@/contexts/ThemeContext'

interface MainLayoutProps {
  children: React.ReactNode
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { theme } = useTheme()

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: theme.colors.bgPrimary,
        color: theme.colors.textPrimary,
      }}
    >
      {children}
    </div>
  )
}