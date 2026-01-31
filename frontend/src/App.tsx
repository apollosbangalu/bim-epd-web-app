import React, { useState } from 'react'
import { ThemeProvider } from './contexts/ThemeContext'
import { TopNav } from './components/layout/TopNav'
import { Sidebar } from './components/layout/Sidebar'
import { ChatWindow } from './components/chat/ChatWindow'
import { ChatInput } from './components/chat/ChatInput'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleSendMessage = async (message: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])

    // TODO: Call API and get response
    // For now, add a placeholder response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Processing your request...',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    }, 500)
  }

  return (
    <ThemeProvider>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <TopNav
          onSemanticClick={() => console.log('Semantic clicked')}
          onGNNClick={() => console.log('GNN clicked')}
          onBDClick={() => console.log('BD clicked')}
          onAPIDocClick={() => window.open('http://localhost:8000/docs', '_blank')}
        />
        
        <div style={{ display: 'flex', flex: 1, marginTop: '60px' }}>
          <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
          
          <main
            style={{
              flex: 1,
              marginLeft: sidebarOpen ? '280px' : '0px',
              transition: 'margin-left 0.3s ease',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <ChatWindow messages={messages} />
            <ChatInput onSend={handleSendMessage} />
          </main>
        </div>
      </div>
    </ThemeProvider>
  )
}

export default App