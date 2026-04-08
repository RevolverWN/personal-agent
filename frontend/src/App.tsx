import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from './stores/authStore'
import Layout from './components/layout/Layout'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Settings from './pages/Settings'
import Files from './pages/Files'
import Memory from './pages/Memory'
import Login from './pages/Login'

function App() {
  const { initialize, isAuthenticated } = useAuthStore()

  useEffect(() => {
    initialize()
  }, [initialize])

  if (!isAuthenticated) {
    return <Login />
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/chat/:conversationId" element={<Chat />} />
        <Route path="/files" element={<Files />} />
        <Route path="/memory" element={<Memory />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
