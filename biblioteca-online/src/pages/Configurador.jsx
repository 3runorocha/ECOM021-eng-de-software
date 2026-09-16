import { useState } from 'react'

const OBRIGATORIAS = [
  { id: 'catalogo', nome: 'Catálogo', porta: 8001, desc: 'Acervo e busca no acervo', camada: 'Serviço' },
  { id: 'usuarios', nome: 'Usuários', porta: 8002, desc: 'Cadastro e autenticação por token', camada: 'Serviço' },
  { id: 'emprestimos', nome: 'Empréstimos', porta: 8003, desc: 'Empréstimo, devolução e multa por atraso', camada: 'Serviço' },
  { id: 'gateway', nome: 'API Gateway', porta: 8000, desc: 'Ponto de entrada único', camada: 'Serviço' },
]

const OPCIONAIS = [
  { id: 'notificacoes', nome: 'Notificações', porta: 8004, desc: 'Alertas de prazo e atraso', camada: 'Serviço' },
  { id: 'recomendacao', nome: 'Recomendação', porta: 8005, desc: 'Sugestões por perfil/histórico', camada: 'Serviço' },
  { id: 'busca_isbn', nome: 'Busca por ISBN', desc: 'Endpoint dedicado de busca no catálogo', camada: 'Componente' },
  { id: 'varredura', nome: 'Varredura automática', desc: 'Geração automática de notificações de prazo', camada: 'Componente', requer: 'notificacoes' },
]

export default function Configurador() {
  const [selecao, setSelecao] = useState({
    notificacoes: false,
    recomendacao: false,
    busca_isbn: false,
    varredura: false,
  })
  const [produto, setProduto] = useState(null)

  function toggle(feature) {
    setSelecao((prev) => {
      const novo = { ...prev, [feature.id]: !prev[feature.id] }
      if (feature.id === 'notificacoes' && !novo.notificacoes) {
        novo.varredura = false
      }
      return novo
    })
    setProduto(null)
  }

  function bloqueada(feature) {
    return feature.requer && !selecao[feature.requer]
  }

  function derivar() {
    const ativas = OPCIONAIS.filter((f) => selecao[f.id])
    const servicos = [
      ...OBRIGATORIAS,
      ...ativas.filter((f) => f.camada === 'Serviço'),
    ]
    setProduto({
      servicos,
      componentes: ativas.filter((f) => f.camada === 'Componente'),
      config: {
        notificacoes: selecao.notificacoes,
        recomendacao: selecao.recomendacao,
        busca_isbn: selecao.busca_isbn,
        varredura: selecao.varredura,
      },
    })
  }

  return (
    <div style={{ padding: '1.5rem', maxWidth: '760px' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '4px' }}>Configurador de produto</h2>
      <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '1.5rem' }}>
        Selecione as features opcionais para derivar um novo produto a partir da linha de produto.
      </p>

      <div style={{ fontSize: '12px', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>
        Features obrigatórias
      </div>
      <div style={{ marginBottom: '1.5rem' }}>
        {OBRIGATORIAS.map((f) => (
          <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0.75rem', background: '#f9fafb', borderRadius: '8px', marginBottom: '6px' }}>
            <input type="checkbox" checked disabled />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '13px', fontWeight: 500, color: '#111' }}>
                {f.nome}{f.porta && <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#9ca3af', marginLeft: '6px' }}>:{f.porta}</span>}
              </div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>{f.desc}</div>
            </div>
            <span style={{ fontSize: '10px', color: '#6b7280', background: '#e5e7eb', padding: '2px 8px', borderRadius: '999px' }}>{f.camada}</span>
          </div>
        ))}
      </div>

      <div style={{ fontSize: '12px', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>
        Features opcionais
      </div>
      <div style={{ marginBottom: '1.5rem' }}>
        {OPCIONAIS.map((f) => {
          const desabilitada = bloqueada(f)
          return (
            <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0.75rem', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', marginBottom: '6px', opacity: desabilitada ? 0.5 : 1 }}>
              <input type="checkbox" checked={selecao[f.id]} disabled={desabilitada} onChange={() => toggle(f)} style={{ cursor: desabilitada ? 'not-allowed' : 'pointer' }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: 500, color: '#111' }}>
                  {f.nome}{f.porta && <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#9ca3af', marginLeft: '6px' }}>:{f.porta}</span>}
                </div>
                <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                  {f.desc}{f.requer && <span style={{ color: '#92400e' }}> — requer {f.requer}</span>}
                </div>
              </div>
              <span style={{ fontSize: '10px', color: '#6b7280', background: '#e5e7eb', padding: '2px 8px', borderRadius: '999px' }}>{f.camada}</span>
            </div>
          )
        })}
      </div>

      <button onClick={derivar} style={{ background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', cursor: 'pointer' }}>
        Derivar produto
      </button>

      {produto && (
        <div style={{ marginTop: '1.5rem', background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '1.25rem' }}>
          <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '0.75rem' }}>Produto derivado</div>

          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Microsserviços que sobem:</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '1rem' }}>
            {produto.servicos.map((s) => (
              <span key={s.id} style={{ fontSize: '12px', background: '#dbeafe', color: '#1d4ed8', padding: '3px 10px', borderRadius: '999px' }}>
                {s.nome}{s.porta && ` :${s.porta}`}
              </span>
            ))}
          </div>

          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Componentes opcionais ativos:</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '1rem' }}>
            {produto.componentes.length === 0
              ? <span style={{ fontSize: '12px', color: '#9ca3af' }}>nenhum</span>
              : produto.componentes.map((c) => (
                <span key={c.id} style={{ fontSize: '12px', background: '#dcfce7', color: '#166534', padding: '3px 10px', borderRadius: '999px' }}>{c.nome}</span>
              ))}
          </div>

          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>config.json do produto:</div>
          <pre style={{ background: '#1e293b', color: '#e2e8f0', padding: '0.75rem', borderRadius: '8px', fontSize: '11px', overflow: 'auto', margin: 0 }}>
{JSON.stringify(produto.config, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}