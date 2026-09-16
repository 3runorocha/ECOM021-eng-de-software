import { useEffect, useState } from 'react'
import { usuariosAPI } from '../services/api'

const MOCK = [
  { id: 1, nome: 'Ana Souza', email: 'ana@biblioteca.br', emprestimos_ativos: 1, data_cadastro: '2026-01-03', ativo: true },
  { id: 2, nome: 'Carlos Lima', email: 'carlos@biblioteca.br', emprestimos_ativos: 1, data_cadastro: '2026-02-15', ativo: true },
  { id: 3, nome: 'João Melo', email: 'joao@biblioteca.br', emprestimos_ativos: 1, data_cadastro: '2026-03-20', ativo: false },
  { id: 4, nome: 'Maria Silva', email: 'maria@biblioteca.br', emprestimos_ativos: 1, data_cadastro: '2026-04-10', ativo: true },
]

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState([])
  const [busca, setBusca] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    usuariosAPI.listar()
      .then((r) => setUsuarios(r.data))
      .catch(() => setUsuarios(MOCK))
      .finally(() => setLoading(false))
  }, [])

  const filtrados = usuarios.filter(
    (u) =>
      u.nome.toLowerCase().includes(busca.toLowerCase()) ||
      u.email.toLowerCase().includes(busca.toLowerCase())
  )

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1.25rem', alignItems: 'center' }}>
        <input
          placeholder="Buscar usuário..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          style={{ maxWidth: '300px', padding: '8px 12px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '13px' }}
        />
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace' }}>
          GET :8002/usuarios
        </span>
      </div>

      {loading ? (
        <p style={{ color: '#9ca3af' }}>Carregando...</p>
      ) : (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                {['Nome', 'Email', 'Empréstimos ativos', 'Cadastro', 'Status'].map((h) => (
                  <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtrados.map((u) => (
                <tr key={u.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '0.75rem 1rem', fontWeight: 500, color: '#111' }}>{u.nome}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>{u.email}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#6b7280', textAlign: 'center' }}>{u.emprestimos_ativos}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>{u.data_cadastro}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span style={{ background: u.ativo ? '#dcfce7' : '#fef3c7', color: u.ativo ? '#166534' : '#92400e', fontSize: '11px', padding: '2px 8px', borderRadius: '999px', fontWeight: 500 }}>
                      {u.ativo ? 'Ativo' : 'Pendente'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
