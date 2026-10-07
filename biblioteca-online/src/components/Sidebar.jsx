import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/useAuth'
import { healthAPI } from '../services/api'
import styles from './Sidebar.module.css'

// O gateway não aparece dentro de /health.servicos, porque é ele quem responde;
// entra separado na primeira linha.
const ROTULOS = {
  imoveis: 'Imóveis',
  usuarios: 'Usuários',
  contratos: 'Contratos',
  notificacoes: 'Notificações',
  recomendacao: 'Recomendação',
}

const INTERVALO_MS = 10000

export default function Sidebar() {
  const { usuario, logout } = useAuth()
  const [saude, setSaude] = useState(null)

  // Esta lista era fixa com ok: true, então mostrava tudo verde mesmo com os
  // serviços derrubados. Agora vem do /health do gateway, que já agrega o
  // estado dos cinco microsserviços.
  useEffect(() => {
    let cancelado = false

    function consultar() {
      healthAPI
        .checar()
        .then((r) => {
          if (!cancelado) setSaude(r.data)
        })
        .catch(() => {
          if (!cancelado) setSaude({ gateway: 'indisponivel', servicos: null })
        })
    }

    consultar()
    const timer = setInterval(consultar, INTERVALO_MS)
    return () => {
      cancelado = true
      clearInterval(timer)
    }
  }, [])

  const linhas = [
    {
      chave: 'gateway',
      label: 'Gateway',
      porta: 8000,
      status: saude ? (saude.gateway === 'ok' ? 'ok' : 'indisponivel') : null,
    },
    ...Object.entries(ROTULOS).map(([chave, label], i) => ({
      chave,
      label,
      porta: saude?.servicos?.[chave]?.porta ?? 8001 + i,
      status: saude ? saude.servicos?.[chave]?.status ?? 'indisponivel' : null,
    })),
  ]

  function corDoPonto(status) {
    if (status === 'ok') return styles.dotGreen
    if (status === null) return styles.dotAmber
    return styles.dotRed
  }

  const degradado = saude?.status_geral && saude.status_geral !== 'ok'

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <div className={styles.logoIcon}>🏠</div>
        <div>
          <div className={styles.logoText}>Aluguel de Imóveis</div>
          <div className={styles.logoSub}>FastAPI + React</div>
        </div>
      </div>

      <nav className={styles.nav}>
        <span className={styles.navLabel}>Principal</span>
        <NavLink to="/" end className={({ isActive }) => isActive ? styles.activeLink : styles.link}>
          🏠 Dashboard
        </NavLink>
        <NavLink to="/imoveis" className={({ isActive }) => isActive ? styles.activeLink : styles.link}>
          🏘️ Imóveis <span className={styles.badge}>8001</span>
        </NavLink>
        <NavLink to="/contratos" className={({ isActive }) => isActive ? styles.activeLink : styles.link}>
          📄 Contratos <span className={styles.badge}>8003</span>
        </NavLink>
        <NavLink to="/usuarios" className={({ isActive }) => isActive ? styles.activeLink : styles.link}>
          👥 Usuários <span className={styles.badge}>8002</span>
        </NavLink>

        <span className={styles.navLabel} style={{ marginTop: '1rem' }}>Serviços</span>
        <NavLink to="/notificacoes" className={({ isActive }) => isActive ? styles.activeLink : styles.link}>
          🔔 Notificações <span className={styles.badge}>8004</span>
        </NavLink>
        <NavLink to="/recomendacao" className={({ isActive }) => isActive ? styles.activeLink : styles.link}>
          ✨ Recomendação <span className={styles.badge}>8005</span>
        </NavLink>
      </nav>

      <div className={styles.status}>
        <div className={styles.statusLabel}>
          Status dos serviços
          {degradado && <span style={{ color: '#b45309', fontWeight: 600 }}> — degradado</span>}
        </div>
        {linhas.map((s) => (
          <div key={s.chave} className={styles.statusRow}>
            <span className={corDoPonto(s.status)} />
            {s.label} — :{s.porta}
            {s.status === null && <span style={{ color: '#9ca3af' }}> (checando)</span>}
          </div>
        ))}
      </div>
      <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '12px', fontWeight: 500, color: '#111', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {usuario?.nome}
          </div>
          <div style={{ fontSize: '11px', color: '#9ca3af' }}>{usuario?.tipo}</div>
        </div>
        <button onClick={logout} title="Sair" style={{ background: 'none', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '5px 10px', fontSize: '12px', cursor: 'pointer', color: '#6b7280' }}>
          Sair
        </button>
      </div>
    </aside>
  )
}
