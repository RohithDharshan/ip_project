import React, { useEffect, useState } from 'react';
import { getAuditLog } from '../api';
import { formatDate } from '../utils';

export default function AuditPage() {
  const [logs,    setLogs]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [search,  setSearch]  = useState('');

  useEffect(() => {
    getAuditLog().then(r => setLogs(r.data)).finally(() => setLoading(false));
  }, []);

  const filtered = logs.filter(l =>
    !search ||
    l.action?.includes(search.toLowerCase()) ||
    String(l.proposal_id)?.includes(search) ||
    String(l.user_id)?.includes(search)
  );

  return (
    <div>
      <div className="page-header">
        <h1>Audit Log</h1>
        <p>Complete immutable trail of all system actions</p>
      </div>

      <div className="card mb-4" style={{ padding: '14px 20px' }}>
        <input
          placeholder="Search by action, proposal ID, user ID…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ maxWidth: 400 }}
        />
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Loading audit log…</div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🔍</div>
            <p>No matching entries.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th><th>Action</th><th>Entity</th>
                  <th>Proposal</th><th>User</th><th>Details</th><th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(l => (
                  <tr key={l.id}>
                    <td className="text-muted text-sm">{l.id}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span>{actionIcon(l.action)}</span>
                        <span style={{ fontWeight: 500, fontSize: '.875rem' }}>
                          {l.action.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase())}
                        </span>
                      </div>
                    </td>
                    <td className="text-sm">
                      {l.entity_type && <span className="chip">{l.entity_type}</span>}
                      {l.entity_id && <span className="text-muted"> #{l.entity_id}</span>}
                    </td>
                    <td className="text-sm">
                      {l.proposal_id ? <span className="chip">Proposal #{l.proposal_id}</span> : '—'}
                    </td>
                    <td className="text-sm text-muted">#{l.user_id || '—'}</td>
                    <td className="text-sm text-muted" style={{ maxWidth: 200 }}>
                      {l.details?.message || l.details?.role
                        ? <span>{l.details.message || l.details.role}</span>
                        : l.details?.routing
                        ? <span>{l.details.routing.join(' → ')}</span>
                        : '—'}
                    </td>
                    <td className="text-sm text-muted">{formatDate(l.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function actionIcon(action) {
  if (action.includes('approved'))    return '✅';
  if (action.includes('rejected'))    return '❌';
  if (action.includes('submitted'))   return '📤';
  if (action.includes('procurement')) return '🛒';
  if (action.includes('clarification'))return '❓';
  return '📝';
}
