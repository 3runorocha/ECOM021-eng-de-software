import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleLogin(e) {
    e.preventDefault()
    setErro('')
    setLoading(true)
    try {
      await login(email, senha)
    } catch {
      setErro('Email ou senha inválidos')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f9fafb' }}>
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '2rem', width: '100%', maxWidth: '360px' }}>
        <div style={{ fontSize: '24px', marginBottom: '4px' }}>📚</div>
        <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '2px' }}>Biblioteca Online</div>
        <div style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '1.5rem' }}>Faça login para continuar</div>

        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '12px' }}>
            <label style={{ fontSize: '12px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>Email</label>
            <input value={email} onChange={e => setEmail(e.target.value)} type="email" required
              style={{ width: '100%', padding: '8px 10px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '13px' }} />
          </div>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ fontSize: '12px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>Senha</label>
            <input value={senha} onChange={e => setSenha(e.target.value)} type="password" required
              style={{ width: '100%', padding: '8px 10px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '13px' }} />
          </div>
          {erro && <div style={{ fontSize: '12px', color: '#991b1b', marginBottom: '12px' }}>{erro}</div>}
          <button type="submit" disabled={loading}
            style={{ width: '100%', background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px', fontSize: '13px', cursor: 'pointer' }}>
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}