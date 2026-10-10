import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/useAuth'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Imoveis from './pages/Imoveis'
import Contratos from './pages/Contratos'
import Usuarios from './pages/Usuarios'
import Notificacoes from './pages/Notificacoes'
import Recomendacao from './pages/Recomendacao'
import Agente from './pages/Agente'

function AppInner() {
  const { usuario } = useAuth()

  if (!usuario) return <Login />

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f9fafb' }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: 'auto' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/imoveis" element={<Imoveis />} />
          <Route path="/contratos" element={<Contratos />} />
          <Route path="/usuarios" element={<Usuarios />} />
          <Route path="/notificacoes" element={<Notificacoes />} />
          <Route path="/recomendacao" element={<Recomendacao />} />
        <Route path="/agente" element={<Agente />} />
          </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppInner />
      </BrowserRouter>
    </AuthProvider>
  )
}