import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getOverview, getProposals, getAuditLog } from '../api';
import { useAuth } from '../App';
import { statusBadge, formatCurrency, formatDate } from '../utils';

export default function DashboardPage() {
  const { user }              = useAuth();
  const navigate              = useNavigate();
  const [overview, setOverview] = useState(null);
  const [recent,   setRecent]   = useState([]);
  const [audits,   setAudits]   = useState([]);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    Promise.all([getOverview(), getProposals({ limit: 5 }), getAuditLog()])
      .then(([ov, pr, al]) => {
        setOverview(ov.data);
        setRecent(pr.data);
        setAudits(al.data.slice(0, 6));
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">⏳ Loading dashboard…</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Welcome back, {user?.name?.split(' ')[0]} 👋</h1>
        <p>Agentic AI–Driven Institutional Workflow Automation</p>
      </div>

      {/* KPI Stats */}
      <div className="stats-grid">
        <div className="stat-card" style={{ borderColor: '#1a237e' }}>
          <div className="stat-value">{overview?.total_proposals ?? 0}</div>
          <div className="stat-label">Total Proposals</div>
        </div>
        <div className="stat-card" style={{ borderColor: '#43a047' }}>
          <div className="stat-value">{overview?.approved_proposals ?? 0}</div>
          <div className="stat-label">Approved</div>
        </div>
        <div className="stat-card" style={{ borderColor: '#fb8c00' }}>
          <div className="stat-value">{overview?.pending_proposals ?? 0}</div>
          <div className="stat-label">Pending Review</div>
        </div>
        <div className="stat-card" style={{ borderColor: '#e53935' }}>
          <div className="stat-value">{overview?.rejected_proposals ?? 0}</div>
          <div className="stat-label">Rejected</div>
        </div>
        <div className="stat-card" style={{ borderColor: '#00bcd4' }}>
          <div className="stat-value">{overview?.approval_rate ?? 0}%</div>
          <div className="stat-label">Approval Rate</div>
        </div>
        <div className="stat-card" style={{ borderColor: '#7b1fa2' }}>
          <div className="stat-value">{overview?.active_vendors ?? 0}</div>
          <div className="stat-label">Active Vendors</div>
        </div>
      </div>

      <div className="grid-2" style={{ gap: 20 }}>
        {/* Recent Proposals */}
        <div className="card">
          <div className="flex-between mb-4">
            <div className="card-title" style={{ margin: 0 }}>📋 Recent Proposals</div>
            <button className="btn btn-outline btn-sm" onClick={() => navigate('/proposals')}>View All</button>
          </div>
          {recent.length === 0 ? (
            <div className="text-muted text-sm">No proposals yet.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Title</th><th>Type</th><th>Budget</th><th>Status</th></tr></thead>
                <tbody>
                  {recent.map(p => (
                    <tr key={p.id} onClick={() => navigate(`/proposals/${p.id}`)} style={{ cursor: 'pointer' }}>
                      <td style={{ fontWeight: 500 }}>{p.title}</td>
                      <td><span className="chip">{p.event_type?.replace('_',' ')}</span></td>
                      <td>{formatCurrency(p.budget)}</td>
                      <td>{statusBadge(p.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Audit */}
        <div className="card">
          <div className="flex-between mb-4">
            <div className="card-title" style={{ margin: 0 }}>🔍 Recent Activity</div>
          </div>
          {audits.length === 0 ? (
            <div className="text-muted text-sm">No activity yet.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {audits.map(a => (
                <div key={a.id} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  <div style={{ fontSize: '1.1rem' }}>{actionIcon(a.action)}</div>
                  <div>
                    <div style={{ fontWeight: 500, fontSize: '.875rem' }}>{humanAction(a.action)}</div>
                    <div className="text-muted text-sm">{formatDate(a.timestamp)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      {user?.role === 'faculty' && (
        <div className="card mt-4">
          <div className="card-title">⚡ Quick Actions</div>
          <div className="flex gap-3">
            <button className="btn btn-primary" onClick={() => navigate('/proposals/new')}>
              ➕ Submit New Proposal
            </button>
            <button className="btn btn-outline" onClick={() => navigate('/proposals')}>
              📋 View My Proposals
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function actionIcon(action) {
  if (action.includes('approved'))   return '✅';
  if (action.includes('rejected'))   return '❌';
  if (action.includes('submitted'))  return '📤';
  if (action.includes('procurement'))return '🛒';
  return '📝';
}
function humanAction(action) {
  return action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
