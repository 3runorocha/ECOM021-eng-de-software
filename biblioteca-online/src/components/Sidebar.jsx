import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Sidebar.module.css'

const servicos = [
  { porta: 8000, label: 'Gateway', ok: true },
  { porta: 8001, label: 'Catálogo', ok: true },
  { porta: 8002, label: 'Usuários', ok: true },
  { porta: 8003, label: 'Empréstimos', ok: true },
  { porta: 8004, label: 'Notificações', ok: false },
  { porta: 8005, label: 'Recomendação', ok: true },
]

export default function Sidebar() {
  const { usuario, logout } = useAuth()
  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <div className={styles.logoIcon}>📚</div>
        <div>
          <div className={styles.logoText}>Biblioteca Online</div>
          <div className={styles.logoSub}>FastAPI + React</div>
        </div>
      </div>

      <nav className={styles.nav}>
        <span className={styles.navLabel}>Principal</span>
        <NavLink to="/" end className={({ isActive }) => isActive ? styles.activeLink : styles.link}>
          🏠 Dashboard
        </NavLink>
        <NavLink to="/catalogo" className={({ isActive }) => isActive ? styles.activeLink : styles.link}>
          📖 Catálogo <span className={styles.badge}>8001</span>
        </NavLink>
        <NavLink to="/emprestimos" className={({ isActive }) => isActive ? styles.activeLink : styles.link}>
          🔄 Empréstimos <span className={styles.badge}>8003</span>
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
        <NavLink to="/configurador" className={({ isActive }) => isActive ? styles.activeLink : styles.link}>
          ⚙️ Configurador
        </NavLink>
      </nav>

      <div className={styles.status}>
        <div className={styles.statusLabel}>Status dos serviços</div>
        {servicos.map((s) => (
          <div key={s.porta} className={styles.statusRow}>
            <span className={s.ok ? styles.dotGreen : styles.dotAmber} />
            {s.label} — :{s.porta}
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
