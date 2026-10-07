import { useEffect, useState } from 'react'
import { imoveisAPI, contratosAPI, usuariosAPI, notificacoesAPI } from '../services/api'
import { useAuth } from '../context/useAuth'

const STATUS = {
  ativo: { label: 'Ativo', color: '#166534', bg: '#dcfce7' },
  atrasado: { label: 'Atrasado', color: '#991b1b', bg: '#fee2e2' },
  encerrado: { label: 'Encerrado', color: '#374151', bg: '#f3f4f6' },
}

const moeda = (v) =>
  v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })

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

export default function Dashboard() {
  const { usuario } = useAuth()
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState(null)
  const [recarga, setRecarga] = useState(0)

  // Esta tela caía num bloco de números fixos (1.247 livros, "Clean Code") quando
  // qualquer chamada falhava -- e uma delas falhava sempre, porque pedia a
  // listagem de notificações sem id de usuário e tomava 422. Agora cada número
  // vem do serviço correspondente, e falha aparece como falha.
  useEffect(() => {
    let cancelado = false

    Promise.all([
      imoveisAPI.listar(),
      contratosAPI.listar(),
      usuariosAPI.listar(),
      notificacoesAPI.listarDoUsuario(usuario.id),
    ])
      .then(([imoveis, contratos, usuarios, notificacoes]) => {
        if (cancelado) return
        setDados({
          imoveis: imoveis.data,
          contratos: contratos.data,
          usuarios: usuarios.data,
          notificacoes: notificacoes.data,
        })
        setErro(null)
      })
      .catch((e) => {
        if (cancelado) return
        setDados(null)
        setErro(
          e.response?.data?.detail ||
            'Não foi possível montar o painel. Os seis serviços estão no ar?'
        )
      })

    return () => {
      cancelado = true
    }
  }, [usuario.id, recarga])

  if (erro) {
    return (
      <div style={{ padding: '1.5rem' }}>
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
            onClick={() => setRecarga((n) => n + 1)}
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
      </div>
    )
  }

  if (!dados) return <p style={{ color: '#6b7280', padding: '2rem' }}>Carregando...</p>

  const disponiveis = dados.imoveis.filter((i) => i.disponivel).length
  const ativos = dados.contratos.filter((c) => c.status === 'ativo').length
  const atrasados = dados.contratos.filter((c) => c.status === 'atrasado').length
  const naoLidas = dados.notificacoes.filter((n) => !n.lida).length
  const receitaMensal = dados.contratos
    .filter((c) => c.status !== 'encerrado')
    .reduce((soma, c) => soma + c.valor_mensal, 0)

  const cartoes = [
    { label: 'Imóveis', valor: dados.imoveis.length, sub: `${disponiveis} disponíveis · :8001` },
    { label: 'Contratos em vigor', valor: ativos + atrasados, sub: `${atrasados} em atraso · :8003` },
    { label: 'Receita mensal contratada', valor: moeda(receitaMensal), sub: 'soma dos contratos em vigor' },
    { label: 'Usuários', valor: dados.usuarios.length, sub: ':8002' },
    { label: 'Suas notificações', valor: dados.notificacoes.length, sub: `${naoLidas} não lida(s) · :8004` },
  ]

  // Os contratos chegam ordenados por data_inicio decrescente do serviço.
  const recentes = dados.contratos.slice(0, 6)
  const nomeImovel = (id) => dados.imoveis.find((i) => i.id === id)?.titulo ?? `Imóvel #${id}`
  const nomeUsuario = (id) => dados.usuarios.find((u) => u.id === id)?.nome ?? `Inquilino #${id}`

  return (
    <div style={{ padding: '1.5rem' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
          gap: '12px',
          marginBottom: '1.5rem',
        }}
      >
        {cartoes.map((c) => (
          <div key={c.label} style={{ background: '#f9fafb', borderRadius: '10px', padding: '1rem' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>{c.label}</div>
            <div style={{ fontSize: '22px', fontWeight: 600, color: '#111' }}>{c.valor}</div>
            <div style={{ fontSize: '11px', color: '#9ca3af', fontFamily: 'monospace' }}>{c.sub}</div>
          </div>
        ))}
      </div>

      <div style={{ fontSize: '13px', fontWeight: 500, color: '#6b7280', marginBottom: '0.75rem' }}>
        Contratos recentes
      </div>
      {recentes.length === 0 ? (
        <p style={{ color: '#9ca3af', fontSize: '13px' }}>
          Nenhum contrato ainda. Rode <code>python seed_contratos.py</code> ou registre um
          na tela de Contratos.
        </p>
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
                {['Imóvel', 'Inquilino', 'Início', 'Fim previsto', 'Aluguel', 'Status'].map((h) => (
                  <th key={h} style={cabecalho}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recentes.map((c) => {
                const s = STATUS[c.status] ?? STATUS.ativo
                return (
                  <tr key={c.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ ...celula, color: '#111', fontWeight: 500 }}>
                      {nomeImovel(c.imovel_id)}
                    </td>
                    <td style={{ ...celula, color: '#6b7280' }}>{nomeUsuario(c.inquilino_id)}</td>
                    <td style={{ ...celula, color: '#6b7280', whiteSpace: 'nowrap' }}>{c.data_inicio}</td>
                    <td style={{ ...celula, color: '#6b7280', whiteSpace: 'nowrap' }}>
                      {c.data_fim_prevista}
                    </td>
                    <td style={{ ...celula, color: '#6b7280', whiteSpace: 'nowrap' }}>
                      {moeda(c.valor_mensal)}
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
