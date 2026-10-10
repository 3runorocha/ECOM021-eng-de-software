import { useEffect, useState } from 'react'
import { agenteAPI } from '../services/api'
import { useAuth } from '../context/useAuth'

const EXEMPLOS = [
  'apartamento de 2 quartos em Maceió até R$ 2.000',
  'tem casa em Recife? qual a mais barata?',
  'quais contratos eu tenho?',
]

const caixa = {
  background: '#fff',
  border: '1px solid #e5e7eb',
  borderRadius: '12px',
  padding: '1rem 1.25rem',
}

export default function Agente() {
  const { usuario } = useAuth()
  const [status, setStatus] = useState(null)
  const [texto, setTexto] = useState('')
  const [conversa, setConversa] = useState([])
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    let cancelado = false
    agenteAPI
      .status()
      .then((r) => {
        if (!cancelado) setStatus(r.data)
      })
      .catch(() => {
        if (!cancelado) setStatus({ credencial_configurada: false, indisponivel: true })
      })
    return () => {
      cancelado = true
    }
  }, [])

  async function perguntar(pergunta) {
    const texto = (pergunta ?? '').trim()
    if (!texto || enviando) return

    setErro(null)
    setEnviando(true)
    setConversa((c) => [...c, { remetente: 'voce', texto }])
    setTexto('')

    try {
      const r = await agenteAPI.perguntar(texto, usuario.id)
      setConversa((c) => [
        ...c,
        {
          remetente: 'agente',
          texto: r.data.resposta,
          ferramentas: r.data.ferramentas_usadas,
          truncado: r.data.truncado,
        },
      ])
    } catch (e) {
      setErro(
        e.response?.data?.detail ||
          'O serviço de agente (:8006) não respondeu.'
      )
    } finally {
      setEnviando(false)
    }
  }

  const semCredencial = status && !status.credencial_configurada

  return (
    <div style={{ padding: '1.5rem', maxWidth: '900px' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
        <span style={{ fontSize: '13px', color: '#6b7280' }}>
          Busca em linguagem natural sobre o portfólio
        </span>
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace' }}>
          POST :8006/agente/perguntar
        </span>
      </div>

      {status && (
        <div
          style={{
            ...caixa,
            marginBottom: '1.25rem',
            fontSize: '13px',
            background: semCredencial ? '#fffbeb' : '#fff',
            borderColor: semCredencial ? '#fde68a' : '#e5e7eb',
            color: semCredencial ? '#92400e' : '#111',
          }}
        >
          {semCredencial ? (
            <>
              <strong style={{ display: 'block', marginBottom: '4px' }}>
                Agente sem credencial
              </strong>
              O serviço está no ar, mas não tem chave da Anthropic. Defina
              <code style={{ margin: '0 4px' }}>ANTHROPIC_API_KEY</code>
              no ambiente e reinicie os serviços. O resto do sistema não depende dele.
            </>
          ) : (
            <>
              Ferramentas disponíveis ao agente:{' '}
              <strong>{(status.ferramentas || []).join(', ')}</strong>. Ele consulta os
              microsserviços pela camada de componentes do framework — não inventa imóvel.
            </>
          )}
        </div>
      )}

      {conversa.length === 0 && !semCredencial && (
        <div style={{ marginBottom: '1.25rem' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px' }}>
            Experimente:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {EXEMPLOS.map((e) => (
              <button
                key={e}
                onClick={() => perguntar(e)}
                disabled={enviando}
                style={{
                  background: 'none',
                  border: '1px solid #e5e7eb',
                  borderRadius: '999px',
                  padding: '6px 12px',
                  fontSize: '12px',
                  cursor: enviando ? 'wait' : 'pointer',
                  color: '#6b7280',
                }}
              >
                {e}
              </button>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '1.25rem' }}>
        {conversa.map((m, i) => (
          <div
            key={i}
            style={{
              ...caixa,
              alignSelf: m.remetente === 'voce' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              background: m.remetente === 'voce' ? '#eff6ff' : '#fff',
              borderColor: m.remetente === 'voce' ? '#bfdbfe' : '#e5e7eb',
            }}
          >
            <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>
              {m.remetente === 'voce' ? 'Você' : 'Agente'}
            </div>
            <div style={{ fontSize: '13px', color: '#111', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
              {m.texto}
            </div>

            {m.ferramentas?.length > 0 && (
              <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid #f3f4f6' }}>
                <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>
                  Ferramentas chamadas
                </div>
                {m.ferramentas.map((f, j) => (
                  <div
                    key={j}
                    style={{ fontSize: '11px', color: '#6b7280', fontFamily: 'monospace' }}
                  >
                    {f.ferramenta}({JSON.stringify(f.argumentos)})
                  </div>
                ))}
              </div>
            )}

            {m.truncado && (
              <div style={{ marginTop: '8px', fontSize: '11px', color: '#92400e' }}>
                Resposta interrompida: o agente atingiu o limite de voltas.
              </div>
            )}
          </div>
        ))}

        {enviando && <div style={{ color: '#9ca3af', fontSize: '13px' }}>O agente está pensando...</div>}
      </div>

      {erro && (
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
          {erro}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault()
          perguntar(texto)
        }}
        style={{ display: 'flex', gap: '8px' }}
      >
        <input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="O que você procura?"
          disabled={enviando}
          style={{
            flex: 1,
            padding: '10px 12px',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            fontSize: '13px',
          }}
        />
        <button
          type="submit"
          disabled={enviando || !texto.trim()}
          style={{
            background: enviando || !texto.trim() ? '#9ca3af' : '#1d4ed8',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            padding: '10px 20px',
            fontSize: '13px',
            cursor: enviando || !texto.trim() ? 'not-allowed' : 'pointer',
          }}
        >
          {enviando ? 'Enviando...' : 'Perguntar'}
        </button>
      </form>
    </div>
  )
}
