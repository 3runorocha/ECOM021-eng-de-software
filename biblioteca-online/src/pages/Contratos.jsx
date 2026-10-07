import { useEffect, useState } from 'react'
import { contratosAPI, imoveisAPI, usuariosAPI } from '../services/api'

const STATUS = {
  ativo: { label: 'Ativo', color: '#166534', bg: '#dcfce7' },
  atrasado: { label: 'Atrasado', color: '#991b1b', bg: '#fee2e2' },
  encerrado: { label: 'Encerrado', color: '#374151', bg: '#f3f4f6' },
}

const moeda = (v) =>
  v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2 })

const celula = { padding: '0.75rem 1rem' }
const cabecalho = {
  padding: '0.75rem 1rem',
  textAlign: 'left',
  fontSize: '11px',
  fontWeight: 600,
  color: '#9ca3af',
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  whiteSpace: 'nowrap',
}
const estiloInput = {
  padding: '8px 10px',
  borderRadius: '8px',
  border: '1px solid #e5e7eb',
  fontSize: '13px',
}

function diasDeAtraso(contrato) {
  const prevista = new Date(contrato.data_fim_prevista + 'T00:00:00')
  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)
  return Math.max(0, Math.round((hoje - prevista) / 86400000))
}

export default function Contratos() {
  const [contratos, setContratos] = useState([])
  const [imoveis, setImoveis] = useState([])
  const [usuarios, setUsuarios] = useState([])
  const [status, setStatus] = useState('')
  const [carregado, setCarregado] = useState(false)
  const [erro, setErro] = useState(null)
  const [acaoErro, setAcaoErro] = useState(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [novo, setNovo] = useState({ inquilino_id: '', imovel_id: '' })
  const [recarga, setRecarga] = useState(0)
  // Encerrar dispara POST + recarga de tres listas pelo gateway, o que leva
  // alguns segundos. Sem isto o botao parece nao ter funcionado.
  const [emAcao, setEmAcao] = useState(null)

  // O filtro de status vai ao serviço de contratos como query param, igual à
  // tela de imóveis: quem filtra é o backend.
  useEffect(() => {
    let cancelado = false

    Promise.all([
      contratosAPI.listar(status ? { status } : {}),
      imoveisAPI.listar(),
      usuariosAPI.listar(),
    ])
      .then(([contratosRes, imoveisRes, usuariosRes]) => {
        if (cancelado) return
        setContratos(contratosRes.data)
        setImoveis(imoveisRes.data)
        setUsuarios(usuariosRes.data)
        setErro(null)
      })
      .catch((e) => {
        if (cancelado) return
        setContratos([])
        setErro(
          e.response?.data?.detail ||
            'Não foi possível carregar os contratos. Os serviços (:8001 a :8003) estão no ar?'
        )
      })
      .finally(() => {
        if (!cancelado) setCarregado(true)
      })

    return () => {
      cancelado = true
    }
  }, [status, recarga])

  const nomeImovel = (id) => imoveis.find((i) => i.id === id)?.titulo ?? `Imóvel #${id}`
  const nomeUsuario = (id) => usuarios.find((u) => u.id === id)?.nome ?? `Inquilino #${id}`
  const disponiveis = imoveis.filter((i) => i.disponivel)

  function recarregar() {
    setRecarga((n) => n + 1)
  }

  async function encerrar(id) {
    setAcaoErro(null)
    setEmAcao(id)
    try {
      await contratosAPI.encerrar(id)
      // Recarrega tudo: encerrar libera o imóvel, então a lista de disponíveis
      // também muda.
      recarregar()
    } catch (e) {
      setAcaoErro(
        e.response?.data?.detail || `Falha ao encerrar o contrato #${id}.`
      )
    } finally {
      setEmAcao(null)
    }
  }

  async function criar(e) {
    e.preventDefault()
    setAcaoErro(null)
    setEmAcao('novo')
    try {
      await contratosAPI.criar({
        inquilino_id: Number(novo.inquilino_id),
        imovel_id: Number(novo.imovel_id),
      })
      setNovo({ inquilino_id: '', imovel_id: '' })
      setMostrarForm(false)
      recarregar()
    } catch (e) {
      setAcaoErro(e.response?.data?.detail || 'Falha ao registrar o contrato.')
    } finally {
      setEmAcao(null)
    }
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1.25rem', alignItems: 'center' }}>
        <select value={status} onChange={(e) => setStatus(e.target.value)} style={estiloInput}>
          <option value="">Todos</option>
          <option value="ativo">Ativos</option>
          <option value="atrasado">Atrasados</option>
          <option value="encerrado">Encerrados</option>
        </select>
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace' }}>
          GET :8003/contratos
        </span>
        <button
          onClick={() => setMostrarForm(!mostrarForm)}
          style={{
            background: '#1d4ed8',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            padding: '8px 14px',
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          + Novo contrato
        </button>
      </div>

      {mostrarForm && (
        <form
          onSubmit={criar}
          style={{
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            padding: '1.25rem',
            marginBottom: '1.25rem',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '12px',
            alignItems: 'end',
          }}
        >
          <div style={{ flex: '1 1 200px' }}>
            <label style={{ fontSize: '12px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
              Inquilino
            </label>
            <select
              value={novo.inquilino_id}
              onChange={(e) => setNovo({ ...novo, inquilino_id: e.target.value })}
              required
              style={{ ...estiloInput, width: '100%' }}
            >
              <option value="">selecione</option>
              {usuarios.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nome}
                </option>
              ))}
            </select>
          </div>
          <div style={{ flex: '1 1 260px' }}>
            <label style={{ fontSize: '12px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
              Imóvel disponível ({disponiveis.length})
            </label>
            <select
              value={novo.imovel_id}
              onChange={(e) => setNovo({ ...novo, imovel_id: e.target.value })}
              required
              style={{ ...estiloInput, width: '100%' }}
            >
              <option value="">selecione</option>
              {disponiveis.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.titulo} — {moeda(i.valor_mensal)}
                </option>
              ))}
            </select>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="submit"
              disabled={disponiveis.length === 0 || emAcao !== null}
              style={{
                background: disponiveis.length === 0 ? '#9ca3af' : '#1d4ed8',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                padding: '8px 16px',
                fontSize: '13px',
                cursor: disponiveis.length === 0 ? 'not-allowed' : 'pointer',
              }}
            >
              {emAcao === 'novo' ? 'Registrando...' : 'Registrar'}
            </button>
            <button
              type="button"
              onClick={() => {
                setMostrarForm(false)
                setAcaoErro(null)
              }}
              style={{
                background: 'none',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '8px 16px',
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              Cancelar
            </button>
          </div>
          <p style={{ flexBasis: '100%', margin: 0, fontSize: '12px', color: '#9ca3af' }}>
            Prazo de 12 meses, contado da assinatura. Só aparecem imóveis sem contrato em
            aberto — um imóvel não aceita dois.
          </p>
        </form>
      )}

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
      ) : contratos.length === 0 ? (
        <p style={{ color: '#9ca3af' }}>Nenhum contrato para esse filtro.</p>
      ) : (
        <div
          style={{
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            overflowX: 'auto',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                {['ID', 'Imóvel', 'Inquilino', 'Início', 'Fim previsto', 'Fim real', 'Aluguel', 'Multa', 'Status', 'Ação'].map((h) => (
                  <th key={h} style={cabecalho}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {contratos.map((c) => {
                const s = STATUS[c.status] ?? STATUS.ativo
                const atraso = c.status === 'atrasado' ? diasDeAtraso(c) : 0
                return (
                  <tr key={c.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ ...celula, color: '#9ca3af', fontFamily: 'monospace', fontSize: '11px' }}>
                      #{c.id}
                    </td>
                    <td style={{ ...celula, fontWeight: 500, color: '#111' }}>
                      {nomeImovel(c.imovel_id)}
                    </td>
                    <td style={{ ...celula, color: '#6b7280' }}>{nomeUsuario(c.inquilino_id)}</td>
                    <td style={{ ...celula, color: '#6b7280', whiteSpace: 'nowrap' }}>{c.data_inicio}</td>
                    <td style={{ ...celula, color: '#6b7280', whiteSpace: 'nowrap' }}>
                      {c.data_fim_prevista}
                      {atraso > 0 && (
                        <div style={{ fontSize: '11px', color: '#991b1b' }}>
                          venceu há {atraso} dia(s)
                        </div>
                      )}
                    </td>
                    <td style={{ ...celula, color: '#6b7280', whiteSpace: 'nowrap' }}>
                      {c.data_fim_real ?? '—'}
                    </td>
                    <td style={{ ...celula, color: '#6b7280', whiteSpace: 'nowrap' }}>
                      {moeda(c.valor_mensal)}
                    </td>
                    <td style={{ ...celula, color: c.multa > 0 ? '#991b1b' : '#6b7280', whiteSpace: 'nowrap' }}>
                      {c.multa > 0 ? moeda(c.multa) : '—'}
                    </td>
                    <td style={celula}>
                      <span
                        style={{
                          background: s.bg,
                          color: s.color,
                          fontSize: '11px',
                          padding: '2px 8px',
                          borderRadius: '999px',
                          fontWeight: 500,
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {s.label}
                      </span>
                    </td>
                    <td style={celula}>
                      {c.status !== 'encerrado' && (
                        <button
                          onClick={() => encerrar(c.id)}
                          disabled={emAcao !== null}
                          style={{
                            background: 'none',
                            border: '1px solid #e5e7eb',
                            borderRadius: '6px',
                            padding: '4px 10px',
                            fontSize: '11px',
                            cursor: emAcao !== null ? 'wait' : 'pointer',
                            color: '#6b7280',
                            whiteSpace: 'nowrap',
                            opacity: emAcao !== null && emAcao !== c.id ? 0.5 : 1,
                          }}
                        >
                          {emAcao === c.id ? 'Encerrando...' : 'Encerrar'}
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

      {carregado && !erro && (
        <p style={{ fontSize: '12px', color: '#9ca3af', marginTop: '10px' }}>
          A multa é calculada pelo serviço de contratos no encerramento: 1/30 do aluguel
          por dia de atraso. A tela mostra os dias em atraso, mas não repete essa regra.
        </p>
      )}
    </div>
  )
}
