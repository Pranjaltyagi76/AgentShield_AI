import { NavLink, Link, Route, Routes, useLocation } from 'react-router-dom'
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  CheckCheck,
  ChevronRight,
  CircleDot,
  Code2,
  Database,
  FlaskConical,
  Layers3,
  LayoutDashboard,
  ListChecks,
  LockKeyhole,
  Menu,
  Network,
  RefreshCw,
  Server,
  ShieldCheck,
  Terminal,
  Workflow,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Button } from './components/ui/button'
import { API_BASE } from './lib/api'
import { cn } from './lib/utils'
import { useSystemStatus } from './lib/use-system-status'

type System = ReturnType<typeof useSystemStatus>
const phases = [
  ['Foundation', 'Application shell, typed API, local database, CI and initial hosting checks.'],
  ['Data & ownership', 'Guest isolation, versioned agent profiles and scenario catalog.'],
  ['Simulation runtime', 'Scripted profiles, mock tools, bounded queue and traces.'],
  ['Policy enforcement', 'Tool permissions, protected records and action boundaries.'],
  ['Scenario evaluation', 'Twelve scenarios, deterministic oracles and evidence-based metrics.'],
  ['Run workspace', 'Launcher, run history, trace timeline and findings.'],
  ['Regression comparison', 'Compatible baselines, improvements and regressions.'],
  ['Optional model adapter', 'Free-tier real-model testing; never required for the demo.'],
  ['Reports & polish', 'HTML/JSON reports, saved sample, accessibility and responsive UX.'],
  ['Deployment validation', 'Verify the complete public workflow and free-service limits.'],
  ['Portfolio readiness', 'Measured evidence, documentation and walkthrough.'],
]
function StatusLabel({ tone, children }: { tone: 'good' | 'muted' | 'warn'; children: ReactNode }) {
  return (
    <span className={cn('status-label', 'status-' + tone)}>
      <span />
      {children}
    </span>
  )
}
function Sidebar({ open, close }: { open: boolean; close: () => void }) {
  return (
    <>
      {open && <button className="nav-backdrop" aria-label="Close navigation" onClick={close} />}
      <aside className={cn('sidebar', open && 'sidebar-open')} aria-label="Primary navigation">
        <Link to="/" className="brand" onClick={close} aria-label="AgentShield AI home">
          <span className="brand-mark">
            <ShieldCheck size={24} strokeWidth={1.7} />
          </span>
          <span>
            AgentShield<span className="brand-ai">AI</span>
          </span>
        </Link>
        <div className="workspace-label">
          <span className="workspace-avatar">PT</span>
          <span>
            Development workspace<small>Pranjal Tyagi</small>
          </span>
          <LockKeyhole size={13} />
        </div>
        <p className="nav-heading">WORKSPACE</p>
        <nav>
          <NavLink to="/" end onClick={close}>
            <LayoutDashboard size={18} />
            Overview
          </NavLink>
          <NavLink to="/system" onClick={close}>
            <Network size={18} />
            System status
          </NavLink>
          <NavLink to="/roadmap" onClick={close}>
            <ListChecks size={18} />
            Development roadmap
          </NavLink>
        </nav>
        <p className="nav-heading nav-heading-later">EVALUATION · COMING LATER</p>
        <div className="future-nav">
          <span>
            <Layers3 size={18} />
            Agents<small>01</small>
          </span>
          <span>
            <FlaskConical size={18} />
            Scenarios<small>01</small>
          </span>
          <span>
            <Workflow size={18} />
            Benchmark runs<small>04</small>
          </span>
          <span>
            <BookOpen size={18} />
            Reports<small>08</small>
          </span>
        </div>
        <div className="sidebar-bottom">
          <div className="safe-mode">
            <ShieldCheck size={18} />
            <div>
              Synthetic by design<small>No real-world tool actions</small>
            </div>
          </div>
          <a
            href="https://github.com/Pranjaltyagi76/AgentShield_AI"
            target="_blank"
            rel="noreferrer"
          >
            <Code2 size={17} />
            View repository
            <ArrowUpRight size={14} />
          </a>
          <div className="sidebar-version">
            <span>v0.1.0</span>
            <span>FOUNDATION</span>
          </div>
        </div>
      </aside>
    </>
  )
}
function SystemCards({ system }: { system: System }) {
  const { health, readiness } = system
  const db = readiness.error ? undefined : readiness.data?.database
  return (
    <div className="system-cards" aria-live="polite">
      <article className="surface system-card">
        <div className="card-top">
          <Server size={19} />
          <StatusLabel
            tone={health.data && !health.error ? 'good' : health.isPending ? 'muted' : 'warn'}
          >
            {health.data && !health.error
              ? 'Connected'
              : health.isPending
                ? 'Checking'
                : 'Unreachable'}
          </StatusLabel>
        </div>
        <h3>API service</h3>
        <p>
          {health.data && !health.error
            ? 'FastAPI is responding to health checks.'
            : health.isPending
              ? 'Checking the backend connection…'
              : 'The backend may be waking or offline.'}
        </p>
        <div className="card-footer">
          <code>GET /api/v1/health</code>
          <span>{health.data && !health.error ? health.data.version : '—'}</span>
        </div>
      </article>
      <article className="surface system-card">
        <div className="card-top">
          <Database size={19} />
          <StatusLabel tone={db === 'connected' ? 'good' : readiness.isPending ? 'muted' : 'warn'}>
            {db === 'connected'
              ? 'Ready'
              : readiness.isPending
                ? 'Checking'
                : db === 'not_configured'
                  ? 'Not configured'
                  : 'Not ready'}
          </StatusLabel>
        </div>
        <h3>Database</h3>
        <p>
          {db === 'connected'
            ? 'PostgreSQL passed the connectivity probe.'
            : db === 'not_configured'
              ? 'Set DATABASE_URL to connect PostgreSQL.'
              : readiness.isPending
                ? 'Checking PostgreSQL readiness…'
                : 'A database connection is not ready yet.'}
        </p>
        <div className="card-footer">
          <code>GET /api/v1/ready</code>
          <span>PostgreSQL</span>
        </div>
      </article>
      <article className="surface system-card">
        <div className="card-top">
          <LockKeyhole size={19} />
          <StatusLabel tone="muted">Disabled in Phase 0</StatusLabel>
        </div>
        <h3>Agent execution</h3>
        <p>Tests and model calls stay unavailable during foundation setup.</p>
        <div className="card-footer">
          <code>No execution endpoints</code>
          <span>Phase 2–4</span>
        </div>
      </article>
    </div>
  )
}
function ArchitectureStrip() {
  return (
    <div className="architecture-strip">
      <div>
        <span className="architecture-icon">
          <Code2 size={21} />
        </span>
        <strong>React + TypeScript</strong>
        <small>Presentation layer</small>
      </div>
      <span className="connection-line">
        <span>HTTPS / REST</span>
        <ArrowRight size={16} />
      </span>
      <div>
        <span className="architecture-icon">
          <Server size={21} />
        </span>
        <strong>Python + FastAPI</strong>
        <small>Application control plane</small>
      </div>
      <span className="connection-line">
        <span>SQL / pooled</span>
        <ArrowRight size={16} />
      </span>
      <div>
        <span className="architecture-icon">
          <Database size={21} />
        </span>
        <strong>PostgreSQL</strong>
        <small>Evidence storage in later phases</small>
      </div>
    </div>
  )
}
function Overview({ system }: { system: System }) {
  return (
    <>
      <div className="eyebrow">
        <span className="eyebrow-line" />
        AI AGENT SECURITY WORKSPACE
      </div>
      <section className="hero">
        <div>
          <h1>
            Test the boundaries.
            <br />
            <span>Trust the evidence.</span>
          </h1>
          <p>
            A controlled space to understand agent behavior,
            <br className="desktop-break" /> enforce tool boundaries, and measure what changes.
          </p>
          <div className="hero-actions">
            <Button asChild>
              <Link to="/system">
                Review system setup
                <ArrowRight size={16} />
              </Link>
            </Button>
            <Button asChild variant="ghost">
              <Link to="/roadmap">
                Explore the roadmap
                <ChevronRight size={16} />
              </Link>
            </Button>
          </div>
        </div>
        <div className="hero-graphic" aria-hidden="true">
          <div className="graphic-grid" />
          <div className="graphic-orbit orbit-one" />
          <div className="graphic-orbit orbit-two" />
          <div className="graphic-core">
            <ShieldCheck size={51} strokeWidth={1.2} />
          </div>
          <span className="graphic-tag tag-policy">
            <CheckCheck size={13} /> POLICY BOUNDARY
          </span>
          <span className="graphic-tag tag-evidence">
            <CircleDot size={13} /> TRACE EVIDENCE
          </span>
          <span className="graphic-node node-one" />
          <span className="graphic-node node-two" />
        </div>
      </section>
      <div className="foundation-notice">
        <span className="notice-icon">
          <Layers3 size={19} />
        </span>
        <div>
          <strong>Phase 0 · Building the foundation</strong>
          <p>This workspace is under development. No security tests have been executed.</p>
        </div>
        <Link to="/roadmap">
          View plan
          <ArrowRight size={15} />
        </Link>
      </div>
      <div className="section-heading">
        <div>
          <h2>Infrastructure at a glance</h2>
          <p>Live connection checks. No sample scores or simulated health.</p>
        </div>
        <Button variant="secondary" onClick={system.refresh} disabled={system.checking}>
          <RefreshCw size={14} className={system.checking ? 'spin' : ''} />
          {system.checking ? 'Checking…' : 'Check connection'}
        </Button>
      </div>
      <SystemCards system={system} />
      <div className="lower-grid">
        <section className="surface architecture-panel">
          <div className="panel-heading">
            <div>
              <h2>One workspace. Clear boundaries.</h2>
              <p>A modular architecture designed for controlled evaluation.</p>
            </div>
            <Network size={19} />
          </div>
          <ArchitectureStrip />
          <div className="panel-footnote">
            <ShieldCheck size={14} />
            Synthetic context. Independent policies. Evidence before claims.
          </div>
        </section>
        <section className="surface next-panel">
          <span className="small-eyebrow">UP NEXT · PHASE 1</span>
          <h2>
            Give every test
            <br />a place to belong.
          </h2>
          <p>Guest isolation, versioned agent profiles, and a curated scenario catalog.</p>
          <Link to="/roadmap">
            See development phases
            <ArrowUpRight size={16} />
          </Link>
        </section>
      </div>
    </>
  )
}
function SystemPage({ system }: { system: System }) {
  const { health, readiness } = system
  const healthPayload = (health.error ? undefined : health.data) ?? {
    status: health.isPending ? 'checking' : 'unreachable',
  }
  const readyPayload = (readiness.error ? undefined : readiness.data) ?? {
    status: readiness.isPending ? 'checking' : 'unreachable',
  }
  return (
    <>
      <div className="eyebrow">
        <span className="eyebrow-line" />
        FOUNDATION / CONNECTIVITY
      </div>
      <div className="page-heading">
        <div>
          <h1>Know what is connected.</h1>
          <p>Health checks measure the process. Readiness checks the database.</p>
        </div>
        <Button variant="secondary" onClick={system.refresh} disabled={system.checking}>
          <RefreshCw size={15} />
          Check connection
        </Button>
      </div>
      <SystemCards system={system} />
      {(health.error || readiness.error) && (
        <div className="connection-error" role="status">
          <strong>Connection needs attention</strong>
          <p>
            {(health.error || readiness.error)?.message} On free hosting, the backend can take about
            a minute to wake. Retry when it is ready.
          </p>
        </div>
      )}
      <div className="surface endpoint-panel">
        <div className="panel-heading">
          <div>
            <h2>API response inspector</h2>
            <p>Current responses from the configured API address.</p>
          </div>
          <Terminal size={19} />
        </div>
        <div className="api-address">
          <span>API BASE</span>
          <code>{API_BASE}</code>
        </div>
        <div className="response-grid">
          <div>
            <h3>
              <span className="http-method">GET</span> /health
            </h3>
            <pre>{JSON.stringify(healthPayload, null, 2)}</pre>
          </div>
          <div>
            <h3>
              <span className="http-method">GET</span> /ready
            </h3>
            <pre>{JSON.stringify(readyPayload, null, 2)}</pre>
          </div>
        </div>
      </div>
      <section className="surface boundary-panel">
        <ShieldCheck size={23} />
        <div>
          <h2>Execution is intentionally unavailable.</h2>
          <p>
            Phase 0 exposes only system checks. Guest sessions, agent configuration, scenarios, and
            benchmark execution arrive in later phases. No inference credentials are required.
          </p>
        </div>
      </section>
    </>
  )
}
function RoadmapPage() {
  return (
    <>
      <div className="eyebrow">
        <span className="eyebrow-line" />
        INCREMENTAL DEVELOPMENT
      </div>
      <div className="page-heading">
        <div>
          <h1>A deliberate path to deployment.</h1>
          <p>Eleven phases. Explicit gates. Free services throughout.</p>
        </div>
        <StatusLabel tone="warn">Phase 0 in progress</StatusLabel>
      </div>
      <p className="roadmap-note">
        Implementation and deployment gates are tracked in the repository. This roadmap describes
        scope; it does not mark unverified work complete.
      </p>
      <div className="surface roadmap-list">
        {phases.map(([title, description], index) => (
          <article key={title} className={cn('roadmap-item', index === 0 && 'roadmap-current')}>
            <span className="phase-number">{String(index).padStart(2, '0')}</span>
            <div>
              <h2>
                {title}
                {index === 7 && <span className="optional-label">Optional</span>}
              </h2>
              <p>{description}</p>
            </div>
            {index === 0 ? (
              <StatusLabel tone="warn">In progress</StatusLabel>
            ) : (
              <span className="planned-label">Planned</span>
            )}
          </article>
        ))}
      </div>
    </>
  )
}
function NotFound() {
  return (
    <div className="empty-page">
      <ShieldCheck size={36} />
      <h1>This page is not here.</h1>
      <p>Return to the foundation workspace.</p>
      <Button asChild>
        <Link to="/">
          Back to overview
          <ArrowRight size={16} />
        </Link>
      </Button>
    </div>
  )
}
export default function App() {
  const [navOpen, setNavOpen] = useState(false)
  const system = useSystemStatus()
  const location = useLocation()
  const mainRef = useRef<HTMLElement>(null)
  const routeName =
    location.pathname === '/'
      ? 'Overview'
      : location.pathname === '/system'
        ? 'System status'
        : location.pathname === '/roadmap'
          ? 'Development roadmap'
          : 'Page not found'
  useEffect(() => {
    document.title = routeName + ' · AgentShield AI'
    mainRef.current?.focus({ preventScroll: true })
  }, [routeName])
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <Sidebar open={navOpen} close={() => setNavOpen(false)} />
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="mobile-menu"
              aria-label={navOpen ? 'Close navigation' : 'Open navigation'}
              aria-expanded={navOpen}
              onClick={() => setNavOpen(!navOpen)}
            >
              {navOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <span>Workspace</span>
            <ChevronRight size={13} />
            <strong>{routeName}</strong>
          </div>
          <div className="topbar-meta">
            <span className="foundation-pill">
              <span />
              Foundation
            </span>
            <span className="owner-avatar" title="Pranjal Tyagi">
              PT
            </span>
          </div>
        </header>
        <main id="main-content" tabIndex={-1} ref={mainRef}>
          <Routes>
            <Route path="/" element={<Overview system={system} />} />
            <Route path="/system" element={<SystemPage system={system} />} />
            <Route path="/roadmap" element={<RoadmapPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
          <footer className="workspace-footer">
            <span>
              <ShieldCheck size={13} />
              AgentShield AI<span className="footer-divider">/</span>Evidence over claims.
            </span>
            <span>
              No paid inference required
              <Check size={13} />
            </span>
          </footer>
        </main>
      </div>
    </div>
  )
}
