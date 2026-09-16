import { createContext, useContext, useState } from 'react'
import { usuariosAPI } from '../services/api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(() => {
    const u = localStorage.getItem('usuario')
    return u ? JSON.parse(u) : null
  })

  async function login(email, senha) {
    const r = await usuariosAPI.login({ email, senha })
    localStorage.setItem('token', r.data.token)
    localStorage.setItem('usuario', JSON.stringify(r.data.usuario))
    setUsuario(r.data.usuario)
  }

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('usuario')
    setUsuario(null)
  }

  return (
    <AuthContext.Provider value={{ usuario, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)