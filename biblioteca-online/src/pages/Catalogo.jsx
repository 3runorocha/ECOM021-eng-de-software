import { useEffect, useState } from 'react'
import { livrosAPI } from '../services/api'

const MOCK = [
  { id: 1, titulo: 'Clean Code', autor: 'Robert C. Martin', isbn: '978-0132350884', genero: 'Tecnologia', disponivel: true },
  { id: 2, titulo: 'Design Patterns', autor: 'Gang of Four', isbn: '978-0201633610', genero: 'Tecnologia', disponivel: false },
  { id: 3, titulo: 'The Pragmatic Programmer', autor: 'Hunt & Thomas', isbn: '978-0135957059', genero: 'Tecnologia', disponivel: true },
  { id: 4, titulo: 'Domain-Driven Design', autor: 'Eric Evans', isbn: '978-0321125217', genero: 'Tecnologia', disponivel: false },
  { id: 5, titulo: 'Refactoring', autor: 'Martin Fowler', isbn: '978-0134757599', genero: 'Tecnologia', disponivel: true },
  { id: 6, titulo: 'Microservices Patterns', autor: 'Chris Richardson', isbn: '978-1617294549', genero: 'Tecnologia', disponivel: true },
]

export default function Catalogo() {
  const [livros, setLivros] = useState([])
  const [busca, setBusca] = useState('')
  const [loading, setLoading] = useState(true)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [novoLivro, setNovoLivro] = useState({ titulo: '', autor: '', isbn: '', genero: '' })

  useEffect(() => {
    livrosAPI.listar()
      .then((r) => setLivros(r.data))
      .catch(() => setLivros(MOCK))
      .finally(() => setLoading(false))
  }, [])

  const filtrados = livros.filter(
    (l) =>
      l.titulo.toLowerCase().includes(busca.toLowerCase()) ||
      l.autor.toLowerCase().includes(busca.toLowerCase())
  )

  async function handleCriar(e) {
    e.preventDefault()
    try {
      const r = await livrosAPI.criar(novoLivro)
      setLivros([...livros, r.data])
    } catch {
      setLivros([...livros, { ...novoLivro, id: Date.now(), disponivel: true }])
    }
    setNovoLivro({ titulo: '', autor: '', isbn: '', genero: '' })
    setMostrarForm(false)
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1.25rem', alignItems: 'center' }}>
        <input
          placeholder="Buscar por título ou autor..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          style={{ maxWidth: '320px', padding: '8px 12px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '13px' }}
        />
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace' }}>
          GET :8001/livros
        </span>
        <button onClick={() => setMostrarForm(!mostrarForm)} style={{ background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: '8px', padding: '8px 14px', fontSize: '13px', cursor: 'pointer' }}>
          + Novo livro
        </button>
      </div>

      {mostrarForm && (
        <form onSubmit={handleCriar} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '1.25rem', marginBottom: '1.25rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          {[['titulo', 'Título'], ['autor', 'Autor'], ['isbn', 'ISBN'], ['genero', 'Gênero']].map(([campo, label]) => (
            <div key={campo}>
              <label style={{ fontSize: '12px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>{label}</label>
              <input
                value={novoLivro[campo]}
                onChange={(e) => setNovoLivro({ ...novoLivro, [campo]: e.target.value })}
                required
                style={{ width: '100%', padding: '7px 10px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '13px' }}
              />
            </div>
          ))}
          <div style={{ gridColumn: '1 / -1', display: 'flex', gap: '8px' }}>
            <button type="submit" style={{ background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: '8px', padding: '8px 16px', fontSize: '13px', cursor: 'pointer' }}>Salvar</button>
            <button type="button" onClick={() => setMostrarForm(false)} style={{ background: 'none', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '8px 16px', fontSize: '13px', cursor: 'pointer' }}>Cancelar</button>
          </div>
        </form>
      )}

      {loading ? (
        <p style={{ color: '#9ca3af' }}>Carregando...</p>
      ) : (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                {['Título', 'Autor', 'ISBN', 'Gênero', 'Disponível'].map((h) => (
                  <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtrados.map((l) => (
                <tr key={l.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '0.75rem 1rem', fontWeight: 500, color: '#111' }}>{l.titulo}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>{l.autor}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#9ca3af', fontFamily: 'monospace', fontSize: '11px' }}>{l.isbn}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>{l.genero}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span style={{ background: l.disponivel ? '#dcfce7' : '#fee2e2', color: l.disponivel ? '#166534' : '#991b1b', fontSize: '11px', padding: '2px 8px', borderRadius: '999px', fontWeight: 500 }}>
                      {l.disponivel ? 'Disponível' : 'Emprestado'}
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
