import { useEffect, useState } from 'react'
import { notificacoesAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'

const MOCK = [
  { id: 1, tipo: 'atraso', mensagem: 'João Melo — livro "Domain-Driven Design" em atraso desde 15/05', criado_em: '2026-05-14T12:00:00', canal: 'email + push' },
  { id: 2, tipo: 'vencimento', mensagem: 'Carlos Lima — devolução de "Design Patterns" vence em 2 dias', criado_em: '2026-05-14T08:00:00', canal: 'email' },
  { id: 3, tipo: 'confirmacao', mensagem: 'Ana Souza — empréstimo de "Clean Code" registrado com sucesso', criado_em: '2026-05-10T10:00:00', canal: 'email' },
  { id: 4, tipo: 'confirmacao', mensagem: 'Maria Silva — novo cadastro confirmado', criado_em: '2026-05-09T09:00:00', canal: 'email' },
]

const TIPO_CONFIG = {
  atraso: { cor: '#991b1b', bg: '#fee2e2', label: 'Atraso' },
  vencimento: { cor: '#92400e', bg: '#fef3c7', label: 'Vencimento' },
  confirmacao: { cor: '#166534', bg: '#dcfce7', label: 'Confirmação' },
}

export default function Notificacoes() {
  const { usuario } = useAuth()
  const [notifs, setNotifs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    notificacoesAPI.listar(usuario.id)
      .then((r) => setNotifs(r.data))
      .catch(() => setNotifs(MOCK))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1.25rem' }}>
        <span style={{ fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace', marginLeft: 'auto' }}>
          GET :8004/notificacoes
        </span>
      </div>

      {loading ? (
        <p style={{ color: '#9ca3af' }}>Carregando...</p>
      ) : (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', overflow: 'hidden' }}>
          {notifs.map((n, i) => {
            const cfg = TIPO_CONFIG[n.tipo] ?? TIPO_CONFIG.confirmacao
            return (
              <div key={n.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '1rem 1.25rem', borderBottom: i < notifs.length - 1 ? '1px solid #f3f4f6' : 'none' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: cfg.cor, marginTop: '5px', flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', color: '#111', lineHeight: 1.5 }}>{n.mensagem}</div>
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>
                    {new Date(n.criado_em).toLocaleString('pt-BR')} — {n.canal}
                  </div>
                </div>
                <span style={{ background: cfg.bg, color: cfg.cor, fontSize: '10px', padding: '2px 8px', borderRadius: '999px', fontWeight: 500, flexShrink: 0 }}>
                  {cfg.label}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
