import { useState } from 'react'
import { recomendacoesAPI, usuariosAPI } from '../services/api'

const USUARIOS_MOCK = [
  { id: 1, nome: 'Ana Souza' },
  { id: 2, nome: 'Carlos Lima' },
  { id: 3, nome: 'João Melo' },
  { id: 4, nome: 'Maria Silva' },
]

const RECS_MOCK = {
  1: [
    { id: 10, titulo: 'The Clean Coder', autor: 'Robert C. Martin', score: 92, motivo: 'Porque você leu Clean Code' },
    { id: 11, titulo: 'Refactoring', autor: 'Martin Fowler', score: 78, motivo: 'Popular entre usuários similares' },
    { id: 12, titulo: 'Working Effectively with Legacy Code', autor: 'Michael Feathers', score: 65, motivo: 'Baseado no seu histórico de gênero' },
  ],
  2: [
    { id: 13, titulo: 'Head First Design Patterns', autor: 'Freeman & Robson', score: 88, motivo: 'Complementa Design Patterns' },
    { id: 14, titulo: 'Clean Architecture', autor: 'Robert C. Martin', score: 75, motivo: 'Popular entre usuários similares' },
  ],
}

export default function Recomendacao() {
  const [usuarioId, setUsuarioId] = useState('1')
  const [recs, setRecs] = useState([])
  const [loading, setLoading] = useState(false)
  const [buscado, setBuscado] = useState(false)

  async function buscar() {
    setLoading(true)
    setBuscado(false)
    try {
      const r = await recomendacoesAPI.porUsuario(usuarioId)
      setRecs(r.data)
    } catch {
      setRecs(RECS_MOCK[usuarioId] ?? RECS_MOCK[1])
    } finally {
      setLoading(false)
      setBuscado(true)
    }
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1.25rem', alignItems: 'center' }}>
        <select
          value={usuarioId}
          onChange={(e) => setUsuarioId(e.target.value)}
          style={{ padding: '8px 10px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '13px' }}
        >
          {USUARIOS_MOCK.map((u) => (
            <option key={u.id} value={u.id}>{u.nome}</option>
          ))}
        </select>
        <button onClick={buscar} style={{ background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: '8px', padding: '8px 16px', fontSize: '13px', cursor: 'pointer' }}>
          ✨ Recomendar
        </button>
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace' }}>
          GET :8005/recomendacoes/{'{user_id}'}
        </span>
      </div>

      <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '1rem' }}>
        Microsserviço de Recomendação — baseado em histórico de empréstimos e perfil do usuário (exigido pelo TES)
      </div>

      {loading && <p style={{ color: '#9ca3af' }}>Calculando recomendações...</p>}

      {buscado && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {recs.map((r) => (
            <div key={r.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '1rem 1.25rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '56px', borderRadius: '6px', background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '22px', flexShrink: 0 }}>
                📘
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '14px', fontWeight: 500, color: '#111' }}>{r.titulo}</div>
                <div style={{ fontSize: '12px', color: '#9ca3af' }}>{r.autor}</div>
                <div style={{ fontSize: '12px', color: '#1d4ed8', marginTop: '4px' }}>{r.motivo}</div>
                <div style={{ marginTop: '6px', height: '4px', background: '#e5e7eb', borderRadius: '999px', width: '120px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${r.score}%`, background: '#1d4ed8', borderRadius: '999px' }} />
                </div>
              </div>
              <span style={{ background: '#eff6ff', color: '#1d4ed8', fontSize: '12px', fontWeight: 600, padding: '4px 10px', borderRadius: '999px', flexShrink: 0 }}>
                {r.score}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
