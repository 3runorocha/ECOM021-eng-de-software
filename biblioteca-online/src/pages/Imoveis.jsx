import { useEffect, useState } from 'react'
import { imoveisAPI } from '../services/api'

const TIPOS = ['apartamento', 'casa']

const FILTROS_VAZIOS = {
  cidade: '',
  tipo: '',
  quartos_min: '',
  valor_max: '',
  disponivel: '',
}

const IMOVEL_VAZIO = {
  titulo: '',
  tipo: 'apartamento',
  endereco: '',
  cidade: '',
  quartos: '',
  banheiros: '',
  area_m2: '',
  valor_mensal: '',
}

const CAMPOS_FORM = [
  ['titulo', 'Título', 'text'],
  ['endereco', 'Endereço', 'text'],
  ['cidade', 'Cidade', 'text'],
  ['quartos', 'Quartos', 'number'],
  ['banheiros', 'Banheiros', 'number'],
  ['area_m2', 'Área (m²)', 'number'],
  ['valor_mensal', 'Aluguel mensal (R$)', 'number'],
]

const moeda = (v) =>
  v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })

const estiloInput = {
  width: '100%',
  padding: '7px 10px',
  borderRadius: '8px',
  border: '1px solid #e5e7eb',
  fontSize: '13px',
}

const estiloBotao = {
  background: '#1d4ed8',
  color: '#fff',
  border: 'none',
  borderRadius: '8px',
  padding: '8px 14px',
  fontSize: '13px',
  cursor: 'pointer',
}

export default function Imoveis() {
  const [imoveis, setImoveis] = useState([])
  const [filtros, setFiltros] = useState(FILTROS_VAZIOS)
  const [busca, setBusca] = useState('')
  const [carregado, setCarregado] = useState(false)
  const [erro, setErro] = useState(null)
  const [mostrarForm, setMostrarForm] = useState(false)
  const [novo, setNovo] = useState(IMOVEL_VAZIO)
  const [erroForm, setErroForm] = useState(null)

  // Os filtros estruturados vão para o backend -- é o serviço de imóveis que
  // filtra, não o navegador. A busca por texto fica no cliente, sobre o
  // resultado, porque o serviço não tem filtro de texto livre.
  //
  // "Carregando..." aparece só na primeira carga: ao trocar um filtro a lista
  // atual continua visível até a resposta chegar. Além de piscar menos, evita
  // setState sincrono no corpo do efeito.
  useEffect(() => {
    const params = {}
    for (const [chave, valor] of Object.entries(filtros)) {
      if (valor !== '') params[chave] = valor
    }

    let cancelado = false
    imoveisAPI
      .listar(params)
      .then((r) => {
        if (cancelado) return
        setImoveis(r.data)
        setErro(null)
      })
      .catch((e) => {
        if (cancelado) return
        setImoveis([])
        setErro(
          e.response?.data?.detail ||
            'Não foi possível falar com o serviço de Imóveis (:8001). Os serviços estão no ar?'
        )
      })
      .finally(() => {
        if (!cancelado) setCarregado(true)
      })

    return () => {
      cancelado = true
    }
  }, [filtros])

  const termo = busca.trim().toLowerCase()
  const visiveis = termo
    ? imoveis.filter(
        (i) =>
          i.titulo.toLowerCase().includes(termo) ||
          i.endereco.toLowerCase().includes(termo)
      )
    : imoveis

  function recarregar() {
    setFiltros({ ...filtros })
  }

  async function handleCriar(e) {
    e.preventDefault()
    setErroForm(null)
    try {
      await imoveisAPI.criar({
        ...novo,
        quartos: Number(novo.quartos),
        banheiros: Number(novo.banheiros),
        area_m2: Number(novo.area_m2),
        valor_mensal: Number(novo.valor_mensal),
      })
      setNovo(IMOVEL_VAZIO)
      setMostrarForm(false)
      recarregar()
    } catch (e) {
      setErroForm(
        e.response?.data?.detail
          ? JSON.stringify(e.response.data.detail)
          : 'Falha ao cadastrar o imóvel.'
      )
    }
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1rem', alignItems: 'center' }}>
        <input
          placeholder="Buscar por título ou endereço..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          style={{ ...estiloInput, maxWidth: '300px' }}
        />
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace' }}>
          GET :8001/imoveis
        </span>
        <button onClick={() => setMostrarForm(!mostrarForm)} style={estiloBotao}>
          + Novo imóvel
        </button>
      </div>

      <div
        style={{
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: '12px',
          padding: '0.875rem 1rem',
          marginBottom: '1.25rem',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '10px',
          alignItems: 'end',
        }}
      >
        <Campo label="Cidade" style={{ flex: '1 1 150px' }}>
          <input
            value={filtros.cidade}
            onChange={(e) => setFiltros({ ...filtros, cidade: e.target.value })}
            placeholder="qualquer"
            style={estiloInput}
          />
        </Campo>
        <Campo label="Tipo" style={{ flex: '1 1 150px' }}>
          <select
            value={filtros.tipo}
            onChange={(e) => setFiltros({ ...filtros, tipo: e.target.value })}
            style={estiloInput}
          >
            <option value="">qualquer</option>
            {TIPOS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </Campo>
        <Campo label="Quartos (mín.)" style={{ flex: '1 1 150px' }}>
          <select
            value={filtros.quartos_min}
            onChange={(e) => setFiltros({ ...filtros, quartos_min: e.target.value })}
            style={estiloInput}
          >
            <option value="">qualquer</option>
            {[1, 2, 3, 4].map((n) => (
              <option key={n} value={n}>
                {n}+
              </option>
            ))}
          </select>
        </Campo>
        <Campo label="Aluguel até (R$)" style={{ flex: '1 1 150px' }}>
          <input
            type="number"
            value={filtros.valor_max}
            onChange={(e) => setFiltros({ ...filtros, valor_max: e.target.value })}
            placeholder="sem limite"
            style={estiloInput}
          />
        </Campo>
        <Campo label="Situação" style={{ flex: '1 1 150px' }}>
          <select
            value={filtros.disponivel}
            onChange={(e) => setFiltros({ ...filtros, disponivel: e.target.value })}
            style={estiloInput}
          >
            <option value="">todas</option>
            <option value="true">disponível</option>
            <option value="false">alugado</option>
          </select>
        </Campo>
        <button
          onClick={() => setFiltros(FILTROS_VAZIOS)}
          style={{
            background: 'none',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: '8px 14px',
            fontSize: '13px',
            cursor: 'pointer',
            color: '#6b7280',
          }}
        >
          Limpar
        </button>
      </div>

      {mostrarForm && (
        <form
          onSubmit={handleCriar}
          style={{
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            padding: '1.25rem',
            marginBottom: '1.25rem',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '12px',
          }}
        >
          <Campo label="Tipo">
            <select
              value={novo.tipo}
              onChange={(e) => setNovo({ ...novo, tipo: e.target.value })}
              style={estiloInput}
            >
              {TIPOS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </Campo>
          {CAMPOS_FORM.map(([campo, label, tipo]) => (
            <Campo key={campo} label={label}>
              <input
                type={tipo}
                step={campo === 'area_m2' ? '0.1' : undefined}
                min={tipo === 'number' ? '0' : undefined}
                value={novo[campo]}
                onChange={(e) => setNovo({ ...novo, [campo]: e.target.value })}
                required
                style={estiloInput}
              />
            </Campo>
          ))}
          {erroForm && (
            <div style={{ gridColumn: '1 / -1', fontSize: '12px', color: '#991b1b' }}>{erroForm}</div>
          )}
          <div style={{ gridColumn: '1 / -1', display: 'flex', gap: '8px' }}>
            <button type="submit" style={estiloBotao}>
              Salvar
            </button>
            <button
              type="button"
              onClick={() => {
                setMostrarForm(false)
                setErroForm(null)
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
        </form>
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
      ) : visiveis.length === 0 ? (
        <p style={{ color: '#9ca3af' }}>Nenhum imóvel para esses filtros.</p>
      ) : (
        <>
          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '10px' }}>
            {visiveis.length} imóvel(is)
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
              gap: '14px',
            }}
          >
            {visiveis.map((i) => (
              <CardImovel key={i.id} imovel={i} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function Campo({ label, children, style }) {
  return (
    <div style={style}>
      <label
        style={{ fontSize: '12px', color: '#6b7280', display: 'block', marginBottom: '4px' }}
      >
        {label}
      </label>
      {children}
    </div>
  )
}

function CardImovel({ imovel }) {
  return (
    <div
      style={{
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'start', gap: '8px' }}>
        <div style={{ fontWeight: 500, color: '#111', fontSize: '14px', flex: 1 }}>
          {imovel.titulo}
        </div>
        <span
          style={{
            background: imovel.disponivel ? '#dcfce7' : '#fee2e2',
            color: imovel.disponivel ? '#166534' : '#991b1b',
            fontSize: '11px',
            padding: '2px 8px',
            borderRadius: '999px',
            fontWeight: 500,
            whiteSpace: 'nowrap',
          }}
        >
          {imovel.disponivel ? 'Disponível' : 'Alugado'}
        </span>
      </div>

      <div style={{ fontSize: '12px', color: '#6b7280' }}>
        {imovel.endereco} — {imovel.cidade}
      </div>

      <div style={{ fontSize: '12px', color: '#6b7280' }}>
        {imovel.tipo} · {imovel.quartos} quarto(s) · {imovel.banheiros} banheiro(s) ·{' '}
        {imovel.area_m2} m²
      </div>

      <div
        style={{
          marginTop: 'auto',
          paddingTop: '8px',
          borderTop: '1px solid #f3f4f6',
          fontSize: '15px',
          fontWeight: 600,
          color: '#111',
        }}
      >
        {moeda(imovel.valor_mensal)}
        <span style={{ fontSize: '12px', fontWeight: 400, color: '#9ca3af' }}> /mês</span>
      </div>
    </div>
  )
}
