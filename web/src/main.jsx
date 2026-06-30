import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from './components/Toast'
import { ThemeProvider } from './context/ThemeContext'
import { ChatProvider } from './context/ChatContext'
import App from './App'
import './themes.css'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <ChatProvider>
          <ToastProvider>
            <App />
          </ToastProvider>
        </ChatProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
)
