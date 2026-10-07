import { useEffect, useState } from 'react'
import { usuariosAPI, contratosAPI } from '../services/api'

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

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState([])
  const [contratos, setContratos] = useState([])
  const [busca, setBusca] = useState('')
  const [carregado, setCarregado] = useState(false)
  const [erro, setErro] = useState(null)
  const [recarga, setRecarga] = useState(0)

  // Esta tela caía num MOCK com e-mails @biblioteca.br e uma coluna de
  // "empréstimos ativos" inventada. Agora a contagem de contratos em vigor é
  // derivada do serviço de contratos.
  useEffect(() => {
    let cancelado = false

    Promise.all([usuariosAPI.listar(), contratosAPI.listar()])
      .then(([usuariosRes, contratosRes]) => {
        if (cancelado) return
        setUsuarios(usuariosRes.data)
        setContratos(contratosRes.data)
        setErro(null)
      })
      .catch((e) => {
        if (cancelado) return
        setUsuarios([])
        setContratos([])
        setErro(
          e.response?.data?.detail ||
            'Não foi possível carregar os usuários (:8002) ou os contratos (:8003).'
        )
      })
      .finally(() => {
        if (!cancelado) setCarregado(true)
      })

    return () => {
      cancelado = true
    }
  }, [recarga])

  const termo = busca.trim().toLowerCase()
  const filtrados = termo
    ? usuarios.filter(
        (u) =>
          u.nome.toLowerCase().includes(termo) || u.email.toLowerCase().includes(termo)
      )
    : usuarios

  function contratosEmVigor(usuarioId) {
    return contratos.filter(
      (c) => c.inquilino_id === usuarioId && c.status !== 'encerrado'
    ).length
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1.25rem', alignItems: 'center' }}>
        <input
          placeholder="Buscar por nome ou e-mail..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          style={{
            maxWidth: '300px',
            padding: '8px 12px',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            fontSize: '13px',
          }}
        />
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af', fontFamily: 'monospace' }}>
          GET :8002/usuarios
        </span>
      </div>

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
      ) : !carregado ? (
        <p style={{ color: '#9ca3af' }}>Carregando...</p>
      ) : filtrados.length === 0 ? (
        <p style={{ color: '#9ca3af' }}>Nenhum usuário encontrado.</p>
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
                {['Nome', 'E-mail', 'Perfil', 'Contratos em vigor', 'Situação'].map((h) => (
                  <th key={h} style={cabecalho}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtrados.map((u) => (
                <tr key={u.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ ...celula, color: '#111', fontWeight: 500 }}>{u.nome}</td>
                  <td style={{ ...celula, color: '#6b7280' }}>{u.email}</td>
                  <td style={{ ...celula, color: '#6b7280' }}>{u.tipo}</td>
                  <td style={{ ...celula, color: '#6b7280' }}>{contratosEmVigor(u.id)}</td>
                  <td style={celula}>
                    <span
                      style={{
                        background: u.ativo ? '#dcfce7' : '#f3f4f6',
                        color: u.ativo ? '#166534' : '#6b7280',
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '999px',
                        fontWeight: 500,
                      }}
                    >
                      {u.ativo ? 'Ativo' : 'Inativo'}
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
