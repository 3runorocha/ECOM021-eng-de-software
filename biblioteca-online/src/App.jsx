import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Catalogo from './pages/Catalogo'
import Emprestimos from './pages/Emprestimos'
import Usuarios from './pages/Usuarios'
import Notificacoes from './pages/Notificacoes'
import Recomendacao from './pages/Recomendacao'
import Configurador from './pages/Configurador'

function AppInner() {
  const { usuario } = useAuth()

  if (!usuario) return <Login />

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f9fafb' }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: 'auto' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/catalogo" element={<Catalogo />} />
          <Route path="/emprestimos" element={<Emprestimos />} />
          <Route path="/usuarios" element={<Usuarios />} />
          <Route path="/notificacoes" element={<Notificacoes />} />
          <Route path="/recomendacao" element={<Recomendacao />} />
          <Route path="/configurador" element={<Configurador />} />
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