import { useEffect, useState } from 'react'
import { emprestimosAPI, livrosAPI, usuariosAPI } from '../services/api'

const STATUS = {
  ativo: { label: 'Ativo', color: '#166534', bg: '#dcfce7' },
  atrasado: { label: 'Atrasado', color: '#991b1b', bg: '#fee2e2' },
  devolvido: { label: 'Devolvido', color: '#374151', bg: '#f3f4f6' },
}

export default function Emprestimos() {
  const [emprestimos, setEmprestimos] = useState([])
  const [livros, setLivros] = useState({})
  const [usuarios, setUsuarios] = useState({})
  const [filtro, setFiltro] = useState('todos')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    carregar()
  }, [])

  async function carregar() {
    setLoading(true)
    try {
      const [empRes, livrosRes, usuariosRes] = await Promise.all([
        emprestimosAPI.listar(),
        livrosAPI.listar(),
        usuariosAPI.listar(),
      ])

      const mapaLivros = {}
      for (const l of livrosRes.data) mapaLivros[l.id] = l.titulo
      setLivros(mapaLivros)

      const mapaUsuarios = {}
      for (const u of usuariosRes.data) mapaUsuarios[u.id] = u.nome
      setUsuarios(mapaUsuarios)

      setEmprestimos(empRes.data)
    } catch {
      setEmprestimos([])
    } finally {
      setLoading(false)
    }
  }

  async function devolver(id) {
    try {
      const r = await emprestimosAPI.devolver(id)
      setEmprestimos((prev) => prev.map((e) => (e.id === id ? r.data : e)))
    } catch {
      // mantém o estado atual em caso de falha
    }
  }

  const filtrados =
    filtro === 'todos' ? emprestimos : emprestimos.filter((e) => e.status === filtro)

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1.25rem', alignItems: 'center' }}>
        <select
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
          style={{ padding: '8px 10px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '13px' }}
        >
          <option value="todos">Todos</option>
          <option value="ativo">Ativos</option>
          <option value="atrasado">Atrasados</option>
          <option value="devolvido">Devolvidos</option>
        </select>
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace' }}>
          GET :8003/emprestimos
        </span>
      </div>

      {loading ? (
        <p style={{ color: '#9ca3af' }}>Carregando...</p>
      ) : (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                {['ID', 'Livro', 'Usuário', 'Empréstimo', 'Devolução', 'Multa', 'Status', 'Ação'].map((h) => (
                  <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtrados.map((e) => {
                const s = STATUS[e.status] ?? STATUS.ativo
                return (
                  <tr key={e.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '0.75rem 1rem', color: '#9ca3af', fontFamily: 'monospace', fontSize: '11px' }}>#{e.id}</td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 500, color: '#111' }}>{livros[e.livro_id] ?? `Livro #${e.livro_id}`}</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>{usuarios[e.usuario_id] ?? `Usuário #${e.usuario_id}`}</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>{e.data_emprestimo}</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>{e.data_devolucao_real ?? '—'}</td>
                    <td style={{ padding: '0.75rem 1rem', color: e.multa > 0 ? '#991b1b' : '#6b7280' }}>
                      {e.multa > 0 ? `R$ ${e.multa.toFixed(2)}` : '—'}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span style={{ background: s.bg, color: s.color, fontSize: '11px', padding: '2px 8px', borderRadius: '999px', fontWeight: 500 }}>{s.label}</span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {e.status !== 'devolvido' && (
                        <button onClick={() => devolver(e.id)} style={{ background: 'none', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '4px 10px', fontSize: '11px', cursor: 'pointer', color: '#6b7280' }}>
                          Devolver
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}