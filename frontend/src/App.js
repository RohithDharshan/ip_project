import React, { createContext, useContext, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, NavLink, useNavigate } from 'react-router-dom';
import { getMe, getPending } from './api'; // used for session re-validation on load

// ── Pages ──────────────────────────────────────────────────────────────────
import LoginPage      from './pages/LoginPage';
import DashboardPage  from './pages/DashboardPage';
import ProposalsPage  from './pages/ProposalsPage';
import NewProposal    from './pages/NewProposal';
import ProposalDetail from './pages/ProposalDetail';
import ApprovalsPage  from './pages/ApprovalsPage';
import VendorsPage    from './pages/VendorsPage';
import AnalyticsPage  from './pages/AnalyticsPage';
import AuditPage      from './pages/AuditPage';

const APPROVER_ROLES = ['hod', 'bursar', 'dean_administration', 'dean_autonomous', 'principal'];

// ── Auth Context ───────────────────────────────────────────────────────────
export const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token  = localStorage.getItem('token');
    const stored = localStorage.getItem('user');
    if (token && stored) {
      // Optimistically restore from cache, then re-validate with server
      try { setUser(JSON.parse(stored)); } catch {}
      getMe()
        .then(res => {
          setUser(res.data);
          localStorage.setItem('user', JSON.stringify(res.data));
        })
        .catch(() => {
          // Token expired or invalid — force re-login
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const setLoggedIn = (userData, token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    sessionStorage.setItem('show_login_notification', '1');
    setUser(userData);
  };

  return (
    <AuthContext.Provider value={{ user, loading, setLoggedIn, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// ── Protected Route ────────────────────────────────────────────────────────
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading">Loading…</div>;
  if (!user)   return <Navigate to="/login" replace />;
  return children;
}

// ── Sidebar ────────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { path: '/',          label: 'Dashboard',  roles: null },
  { path: '/proposals', label: 'Proposals',  roles: null },
  { path: '/approvals', label: 'Approvals',  roles: ['hod','bursar','dean_administration','dean_autonomous','principal','admin'] },
  { path: '/vendors',   label: 'Vendors',    roles: null },
  { path: '/analytics', label: 'Analytics',  roles: null },
  { path: '/audit',     label: 'Audit Log',  roles: ['admin','principal','bursar'] },
];

function Sidebar() {
  const { user, logout } = useAuth();
  const navigate         = useNavigate();
  const [pending, setPending] = useState([]);
  const [notifOpen, setNotifOpen] = useState(false);

  const handleLogout = () => { logout(); navigate('/login'); };
  const visibleItems = NAV_ITEMS.filter(
    item => !item.roles || item.roles.includes(user?.role)
  );

  useEffect(() => {
    if (!APPROVER_ROLES.includes(user?.role)) {
      setPending([]);
      setNotifOpen(false);
      return;
    }

    let mounted = true;

    const loadPending = () => {
      getPending()
        .then(res => {
          if (!mounted) return;
          const items = Array.isArray(res.data) ? res.data : [];
          setPending(items);
        })
        .catch(() => {
          if (!mounted) return;
          setPending([]);
        });
    };

    loadPending();
    const timer = setInterval(loadPending, 60000);

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, [user?.role]);

  const preview = pending.slice(0, 3);

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h2>AgentFlow</h2>
        <small>PSG AI Consortium</small>
      </div>

      <div className="user-badge">
        <div className="user-avatar">{user?.name?.[0] || 'U'}</div>
        <div>
          <div style={{ fontSize: '.85rem', fontWeight: 600 }}>{user?.name}</div>
          <div style={{ fontSize: '.7rem', opacity: .7, textTransform: 'capitalize' }}>{user?.role?.replace('_',' ')}</div>
        </div>
      </div>

      {APPROVER_ROLES.includes(user?.role) && (
        <div className="sidebar-notifications">
          <button
            className="notif-trigger"
            onClick={() => setNotifOpen(v => !v)}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 3a6 6 0 0 0-6 6v3.4c0 .9-.3 1.8-.9 2.5L3.6 17h16.8l-1.5-2.1a4.4 4.4 0 0 1-.9-2.5V9a6 6 0 0 0-6-6Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M9.5 19a2.5 2.5 0 0 0 5 0" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
            </svg>
            <span>Notifications</span>
            {pending.length > 0 && <span className="notif-count">{pending.length}</span>}
          </button>

          {notifOpen && (
            <div className="notif-panel">
              {pending.length === 0 ? (
                <div className="notif-empty">No pending approvals.</div>
              ) : (
                <>
                  {preview.map(item => (
                    <button
                      key={item.id}
                      className="notif-item"
                      onClick={() => {
                        setNotifOpen(false);
                        navigate('/approvals');
                      }}
                    >
                      <div className="notif-title">{item.proposal_title}</div>
                      <div className="notif-meta">Step {item.step_order}</div>
                    </button>
                  ))}
                  <button
                    className="notif-view-all"
                    onClick={() => {
                      setNotifOpen(false);
                      navigate('/approvals');
                    }}
                  >
                    Open Approvals
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      )}

      <nav className="sidebar-nav">
        {visibleItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
              {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button
          className="btn btn-outline btn-sm"
          style={{ width: '100%', color: 'rgba(255,255,255,.8)', border: '1px solid rgba(255,255,255,.3)' }}
          onClick={handleLogout}
        >
          Logout
        </button>
      </div>
    </aside>
  );
}

function LoginNotificationPopup() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState([]);

  useEffect(() => {
    const shouldShow = sessionStorage.getItem('show_login_notification') === '1';

    if (!shouldShow || !APPROVER_ROLES.includes(user?.role)) return;

    getPending()
      .then(res => {
        const items = Array.isArray(res.data) ? res.data : [];
        if (items.length > 0) {
          setPending(items);
          setOpen(true);
        }
      })
      .catch(() => {
        // Silent fail: login flow should not break if notification fetch fails.
      })
      .finally(() => {
        sessionStorage.removeItem('show_login_notification');
      });
  }, [user]);

  if (!open) return null;

  const preview = pending.slice(0, 3);

  return (
    <div className="modal-overlay" onClick={() => setOpen(false)}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h2>Pending Approvals</h2>
        <div className="alert alert-info" style={{ marginBottom: 12 }}>
          You have <strong>{pending.length}</strong> pending approval{pending.length > 1 ? 's' : ''}.
        </div>

        <div style={{ marginBottom: 16 }}>
          {preview.map(item => (
            <div key={item.id} style={{ padding: '8px 0', borderBottom: '1px solid #e2e8f0' }}>
              <div style={{ fontWeight: 600 }}>{item.proposal_title}</div>
              <div className="text-sm text-muted">Step {item.step_order} • {item.approver_role.replace(/_/g, ' ')}</div>
            </div>
          ))}
        </div>

        <div className="modal-actions">
          <button className="btn btn-outline" onClick={() => setOpen(false)}>Dismiss</button>
          <button
            className="btn btn-primary"
            onClick={() => {
              setOpen(false);
              navigate('/approvals');
            }}
          >
            Open Approvals
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Layout ─────────────────────────────────────────────────────────────────
function AppLayout({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">{children}</main>
      <LoginNotificationPopup />
    </div>
  );
}

// ── App ────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route path="/*" element={
            <ProtectedRoute>
              <AppLayout>
                <Routes>
                  <Route path="/"                    element={<DashboardPage />} />
                  <Route path="/proposals"           element={<ProposalsPage />} />
                  <Route path="/proposals/new"       element={<NewProposal />} />
                  <Route path="/proposals/:id"       element={<ProposalDetail />} />
                  <Route path="/approvals"           element={<ApprovalsPage />} />
                  <Route path="/vendors"             element={<VendorsPage />} />
                  <Route path="/analytics"           element={<AnalyticsPage />} />
                  <Route path="/audit"               element={<AuditPage />} />
                  <Route path="*"                    element={<Navigate to="/" replace />} />
                </Routes>
              </AppLayout>
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
