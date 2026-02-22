import React, { createContext, useContext, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, NavLink, useNavigate } from 'react-router-dom';
import { getMe } from './api';

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

// ── Auth Context ───────────────────────────────────────────────────────────
export const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('user');
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch {}
    }
    setLoading(false);
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const setLoggedIn = (userData, token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
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
  { path: '/',          label: 'Dashboard',  icon: '📊', roles: null },
  { path: '/proposals', label: 'Proposals',  icon: '📋', roles: null },
  { path: '/approvals', label: 'Approvals',  icon: '✅', roles: ['coordinator','hod','programme_manager','principal','bursar','admin'] },
  { path: '/vendors',   label: 'Vendors',    icon: '🏪', roles: null },
  { path: '/analytics', label: 'Analytics',  icon: '📈', roles: null },
  { path: '/audit',     label: 'Audit Log',  icon: '🔍', roles: ['admin','principal','bursar'] },
];

function Sidebar() {
  const { user, logout } = useAuth();
  const navigate         = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };
  const visibleItems = NAV_ITEMS.filter(
    item => !item.roles || item.roles.includes(user?.role)
  );

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h2>🤖 AgentFlow</h2>
        <small>PSG AI Consortium</small>
      </div>

      <div className="user-badge">
        <div className="user-avatar">{user?.name?.[0] || 'U'}</div>
        <div>
          <div style={{ fontSize: '.85rem', fontWeight: 600 }}>{user?.name}</div>
          <div style={{ fontSize: '.7rem', opacity: .7, textTransform: 'capitalize' }}>{user?.role?.replace('_',' ')}</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {visibleItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span className="icon">{item.icon}</span>
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
          🚪 Logout
        </button>
      </div>
    </aside>
  );
}

// ── Layout ─────────────────────────────────────────────────────────────────
function AppLayout({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">{children}</main>
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
