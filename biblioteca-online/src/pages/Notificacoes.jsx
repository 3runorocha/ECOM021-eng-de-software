import { useEffect, useState } from 'react'
import { notificacoesAPI } from '../services/api'
import { useAuth } from '../context/useAuth'

// Os tipos são os que o backend realmente emite: o serviço de contratos manda
// contrato_confirmado, e a varredura do serviço de notificações gera atraso e
// prazo_proximo.
const TIPOS = {
  atraso: { cor: '#991b1b', bg: '#fee2e2', label: 'Atraso' },
  prazo_proximo: { cor: '#92400e', bg: '#fef3c7', label: 'Vence em breve' },
  contrato_confirmado: { cor: '#166534', bg: '#dcfce7', label: 'Contrato' },
}

const TIPO_PADRAO = { cor: '#374151', bg: '#f3f4f6', label: 'Aviso' }

const botaoSecundario = {
  background: 'none',
  border: '1px solid #e5e7eb',
  borderRadius: '8px',
  padding: '8px 14px',
  fontSize: '13px',
  cursor: 'pointer',
  color: '#6b7280',
}

export default function Notificacoes() {
  const { usuario } = useAuth()
  const [notificacoes, setNotificacoes] = useState([])
  const [carregado, setCarregado] = useState(false)
  const [erro, setErro] = useState(null)
  const [acaoErro, setAcaoErro] = useState(null)
  const [emAcao, setEmAcao] = useState(false)
  const [recarga, setRecarga] = useState(0)

  // A tela antiga lia criado_em e canal, campos que o modelo não tem, e caía
  // num MOCK de livros quando a chamada falhava.
  useEffect(() => {
    let cancelado = false

    notificacoesAPI
      .listarDoUsuario(usuario.id)
      .then((r) => {
        if (cancelado) return
        setNotificacoes(r.data)
        setErro(null)
      })
      .catch((e) => {
        if (cancelado) return
        setNotificacoes([])
        setErro(
          e.response?.data?.detail ||
            'Não foi possível carregar as notificações (:8004).'
        )
      })
      .finally(() => {
        if (!cancelado) setCarregado(true)
      })

    return () => {
      cancelado = true
    }
  }, [usuario.id, recarga])

  const recarregar = () => setRecarga((n) => n + 1)
  const naoLidas = notificacoes.filter((n) => !n.lida).length

  async function executar(acao) {
    setAcaoErro(null)
    setEmAcao(true)
    try {
      await acao()
      recarregar()
    } catch (e) {
      setAcaoErro(e.response?.data?.detail || 'A ação falhou.')
    } finally {
      setEmAcao(false)
    }
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1.25rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '13px', color: '#6b7280' }}>
          {naoLidas} não lida(s) de {notificacoes.length}
        </span>
        <button
          onClick={() => executar(() => notificacoesAPI.varredura())}
          disabled={emAcao}
          style={botaoSecundario}
          title="Faz o serviço varrer os contratos e gerar alertas de atraso e vencimento"
        >
          {emAcao ? 'Executando...' : 'Rodar varredura'}
        </button>
        <button
          onClick={() => executar(() => notificacoesAPI.marcarTodasLidas(usuario.id))}
          disabled={emAcao || naoLidas === 0}
          style={{ ...botaoSecundario, opacity: naoLidas === 0 ? 0.5 : 1 }}
        >
          Marcar todas como lidas
        </button>
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace' }}>
          GET :8004/notificacoes/usuario/{usuario.id}
        </span>
      </div>

      {acaoErro && (
        <div
          style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '12px',
            padding: '0.75rem 1rem',
            marginBottom: '1rem',
            color: '#991b1b',
            fontSize: '13px',
          }}
        >
          {acaoErro}
        </div>
      )}

      {erro ? (
        <div
          style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            color: '#991b1b',
            fontSize: '13px',
          }}
        >
          <strong style={{ display: 'block', marginBottom: '4px' }}>Falha ao carregar</strong>
          {erro}
          <button
            onClick={recarregar}
            style={{
              display: 'block',
              marginTop: '10px',
              background: 'none',
              border: '1px solid #fecaca',
              borderRadius: '8px',
              padding: '6px 12px',
              fontSize: '12px',
              cursor: 'pointer',
              color: '#991b1b',
            }}
          >
            Tentar de novo
          </button>
        </div>
      ) : !carregado ? (
        <p style={{ color: '#9ca3af' }}>Carregando...</p>
      ) : notificacoes.length === 0 ? (
        <p style={{ color: '#9ca3af', fontSize: '13px' }}>
          Nenhuma notificação. Registre um contrato, ou use "Rodar varredura" para que o
          serviço gere alertas dos contratos vencidos.
        </p>
      ) : (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', overflow: 'hidden' }}>
          {notificacoes.map((n, i) => {
            const cfg = TIPOS[n.tipo] ?? TIPO_PADRAO
            return (
              <div
                key={n.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '1rem 1.25rem',
                  borderBottom: i < notificacoes.length - 1 ? '1px solid #f3f4f6' : 'none',
                  background: n.lida ? '#fff' : '#f9fafb',
                }}
              >
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: n.lida ? '#e5e7eb' : cfg.cor,
                    marginTop: '5px',
                    flexShrink: 0,
                  }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', color: '#111', lineHeight: 1.5 }}>{n.mensagem}</div>
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>
                    {new Date(n.data_criacao).toLocaleString('pt-BR')}
                    {n.imovel_id != null && ` — imóvel #${n.imovel_id}`}
                  </div>
                </div>
                {!n.lida && (
                  <button
                    onClick={() => executar(() => notificacoesAPI.marcarLida(n.id))}
                    disabled={emAcao}
                    style={{
                      background: 'none',
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px',
                      padding: '4px 10px',
                      fontSize: '11px',
                      cursor: 'pointer',
                      color: '#6b7280',
                      flexShrink: 0,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    Marcar lida
                  </button>
                )}
                <span
                  style={{
                    background: cfg.bg,
                    color: cfg.cor,
                    fontSize: '10px',
                    padding: '2px 8px',
                    borderRadius: '999px',
                    fontWeight: 500,
                    flexShrink: 0,
                  }}
                >
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
