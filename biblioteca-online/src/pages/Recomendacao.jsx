import { useEffect, useState } from 'react'
import { recomendacoesAPI, usuariosAPI } from '../services/api'

// Score máximo do serviço: 3 pontos por tipo preferido + 2 por cidade preferida.
// A tela antiga mostrava o score como porcentagem, o que não correspondia a nada.
const SCORE_MAXIMO = 5

const moeda = (v) =>
  v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })

export default function Recomendacao() {
  const [usuarios, setUsuarios] = useState([])
  const [usuarioId, setUsuarioId] = useState('')
  const [perfil, setPerfil] = useState(null)
  const [recomendacoes, setRecomendacoes] = useState([])
  const [buscando, setBuscando] = useState(false)
  const [buscado, setBuscado] = useState(false)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    let cancelado = false
    usuariosAPI
      .listar()
      .then((r) => {
        if (cancelado) return
        setUsuarios(r.data)
        if (r.data.length > 0) setUsuarioId(String(r.data[0].id))
      })
      .catch(() => {
        if (!cancelado) setErro('Não foi possível carregar os usuários (:8002).')
      })
    return () => {
      cancelado = true
    }
  }, [])

  async function buscar() {
    if (!usuarioId) return
    setBuscando(true)
    setErro(null)
    try {
      const [recsRes, perfilRes] = await Promise.all([
        recomendacoesAPI.porUsuario(usuarioId),
        recomendacoesAPI.perfil(usuarioId),
      ])
      setRecomendacoes(recsRes.data)
      setPerfil(perfilRes.data)
      setBuscado(true)
    } catch (e) {
      setRecomendacoes([])
      setPerfil(null)
      setBuscado(false)
      setErro(
        e.response?.data?.detail ||
          'O serviço de Recomendação (:8005) não respondeu. Ele depende de Contratos (:8003) e Imóveis (:8001).'
      )
    } finally {
      setBuscando(false)
    }
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <select
          value={usuarioId}
          onChange={(e) => setUsuarioId(e.target.value)}
          style={{ padding: '8px 10px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '13px' }}
        >
          {usuarios.length === 0 && <option value="">carregando...</option>}
          {usuarios.map((u) => (
            <option key={u.id} value={u.id}>
              {u.nome}
            </option>
          ))}
        </select>
        <button
          onClick={buscar}
          disabled={buscando || !usuarioId}
          style={{
            background: buscando || !usuarioId ? '#9ca3af' : '#1d4ed8',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            padding: '8px 16px',
            fontSize: '13px',
            cursor: buscando || !usuarioId ? 'wait' : 'pointer',
          }}
        >
          {buscando ? 'Calculando...' : '✨ Recomendar imóveis'}
        </button>
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace' }}>
          GET :8005/recomendacao/{usuarioId || '{id}'}
        </span>
      </div>

      <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '1.25rem' }}>
        O serviço monta o perfil a partir do histórico de contratos do inquilino (tipos e
        cidades que ele já alugou) e pontua os imóveis disponíveis. Na Fase 4 esta tela
        ganha a interface do agente, que faz a busca em linguagem natural.
      </div>

      {erro && (
        <div
          style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            color: '#991b1b',
            fontSize: '13px',
            marginBottom: '1.25rem',
          }}
        >
          <strong style={{ display: 'block', marginBottom: '4px' }}>Falha</strong>
          {erro}
        </div>
      )}

      {buscado && perfil && (
        <div
          style={{
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            marginBottom: '1.25rem',
            fontSize: '13px',
          }}
        >
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px' }}>
            Perfil calculado
          </div>
          <div style={{ color: '#111' }}>
            {perfil.total_contratos} contrato(s) no histórico
            {perfil.tipos_favoritos.length > 0 && (
              <> · prefere <strong>{perfil.tipos_favoritos.join(', ')}</strong></>
            )}
            {perfil.cidades_favoritas.length > 0 && (
              <> · em <strong>{perfil.cidades_favoritas.join(', ')}</strong></>
            )}
          </div>
          {perfil.total_contratos === 0 && (
            <div style={{ color: '#9ca3af', marginTop: '4px', fontSize: '12px' }}>
              Sem histórico, o serviço não tem preferência para pontuar — a lista vem vazia.
            </div>
          )}
        </div>
      )}

      {buscado && !buscando && (
        recomendacoes.length === 0 ? (
          <p style={{ color: '#9ca3af', fontSize: '13px' }}>
            Nenhuma recomendação com score positivo para esse inquilino.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {recomendacoes.map((r) => (
              <div
                key={r.imovel_id}
                style={{
                  background: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '12px',
                  padding: '1rem 1.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                }}
              >
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '8px',
                    background: '#eff6ff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '20px',
                    flexShrink: 0,
                  }}
                >
                  {r.tipo === 'casa' ? '🏡' : '🏢'}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: '#111' }}>{r.titulo}</div>
                  <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                    {r.tipo} · {r.cidade}
                    {r.valor_mensal != null && <> · {moeda(r.valor_mensal)}/mês</>}
                  </div>
                  <div style={{ fontSize: '12px', color: '#1d4ed8', marginTop: '4px' }}>{r.motivo}</div>
                  <div
                    style={{
                      marginTop: '6px',
                      height: '4px',
                      background: '#e5e7eb',
                      borderRadius: '999px',
                      width: '120px',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${Math.min(100, (r.score / SCORE_MAXIMO) * 100)}%`,
                        background: '#1d4ed8',
                        borderRadius: '999px',
                      }}
                    />
                  </div>
                </div>
                <span
                  style={{
                    background: '#eff6ff',
                    color: '#1d4ed8',
                    fontSize: '12px',
                    fontWeight: 600,
                    padding: '4px 10px',
                    borderRadius: '999px',
                    flexShrink: 0,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {r.score} / {SCORE_MAXIMO}
                </span>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
