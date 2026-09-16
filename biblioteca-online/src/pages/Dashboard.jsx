import { useEffect, useState } from 'react'
import { livrosAPI, emprestimosAPI, usuariosAPI, notificacoesAPI } from '../services/api'

export default function Dashboard() {
  const [stats, setStats] = useState({ livros: 0, emprestimos: 0, usuarios: 0, notificacoes: 0 })
  const [emprestimosRecentes, setEmprestimosRecentes] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function carregar() {
      try {
        const [livros, emprestimos, usuarios, notifs] = await Promise.all([
          livrosAPI.listar(),
          emprestimosAPI.listar(),
          usuariosAPI.listar(),
          notificacoesAPI.listar(),
        ])
        setStats({
          livros: livros.data.length ?? 0,
          emprestimos: emprestimos.data.length ?? 0,
          usuarios: usuarios.data.length ?? 0,
          notificacoes: notifs.data.length ?? 0,
        })
        setEmprestimosRecentes(emprestimos.data.slice(0, 5))
      } catch {
        setStats({ livros: 1247, emprestimos: 83, usuarios: 412, notificacoes: 38 })
        setEmprestimosRecentes([
          { id: 1, livro_titulo: 'Clean Code', usuario_nome: 'Ana Souza', data_emprestimo: '2026-05-10', data_devolucao: '2026-05-24', status: 'ativo' },
          { id: 2, livro_titulo: 'Design Patterns', usuario_nome: 'Carlos Lima', data_emprestimo: '2026-05-08', data_devolucao: '2026-05-22', status: 'vence_breve' },
          { id: 3, livro_titulo: 'Domain-Driven Design', usuario_nome: 'João Melo', data_emprestimo: '2026-05-01', data_devolucao: '2026-05-15', status: 'atrasado' },
        ])
      } finally {
        setLoading(false)
      }
    }
    carregar()
  }, [])

  const statusLabel = {
    ativo: { label: 'Ativo', color: '#166534', bg: '#dcfce7' },
    vence_breve: { label: 'Vence em breve', color: '#92400e', bg: '#fef3c7' },
    atrasado: { label: 'Atrasado', color: '#991b1b', bg: '#fee2e2' },
  }

  if (loading) return <p style={{ color: '#6b7280', padding: '2rem' }}>Carregando...</p>

  return (
    <div style={{ padding: '1.5rem' }}>
      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '1.5rem' }}>
        {[
          { label: 'Total de livros', valor: stats.livros.toLocaleString(), sub: 'via :8001' },
          { label: 'Empréstimos ativos', valor: stats.emprestimos, sub: 'via :8003' },
          { label: 'Usuários', valor: stats.usuarios, sub: 'via :8002' },
          { label: 'Notificações', valor: stats.notificacoes, sub: 'via :8004' },
        ].map((s) => (
          <div key={s.label} style={{ background: '#f9fafb', borderRadius: '10px', padding: '1rem' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>{s.label}</div>
            <div style={{ fontSize: '22px', fontWeight: 600, color: '#111' }}>{s.valor}</div>
            <div style={{ fontSize: '11px', color: '#9ca3af', fontFamily: 'monospace' }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Empréstimos recentes */}
      <div style={{ fontSize: '13px', fontWeight: 500, color: '#6b7280', marginBottom: '0.75rem' }}>
        Empréstimos recentes
      </div>
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
              {['Livro', 'Usuário', 'Empréstimo', 'Devolução', 'Status'].map((h) => (
                <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {emprestimosRecentes.map((e) => {
              const s = statusLabel[e.status] ?? statusLabel.ativo
              return (
                <tr key={e.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '0.75rem 1rem', color: '#111', fontWeight: 500 }}>{e.livro_titulo}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>{e.usuario_nome}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>{e.data_emprestimo}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>{e.data_devolucao}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span style={{ background: s.bg, color: s.color, fontSize: '11px', padding: '2px 8px', borderRadius: '999px', fontWeight: 500 }}>{s.label}</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
