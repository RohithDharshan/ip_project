import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProposals, deleteProposal } from '../api';
import { useAuth } from '../App';
import { statusBadge, formatCurrency, eventLabel, formatDate } from '../utils';

export default function ProposalsPage() {
  const { user }              = useAuth();
  const navigate              = useNavigate();
  const [proposals, setProposals] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [filter,    setFilter]    = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const res = await getProposals(filter ? { status: filter } : {});
      setProposals(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filter]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this proposal?')) return;
    await deleteProposal(id);
    load();
  };

  return (
    <div>
      <div className="flex-between mb-6">
        <div className="page-header" style={{ margin: 0 }}>
          <h1>📋 Proposals</h1>
          <p>All institutional event proposals</p>
        </div>
        {(user?.role === 'faculty' || user?.role === 'coordinator') && (
          <button className="btn btn-primary" onClick={() => navigate('/proposals/new')}>
            ➕ New Proposal
          </button>
        )}
      </div>

      {/* Filter bar */}
      <div className="card mb-4" style={{ padding: '14px 20px' }}>
        <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
          {['', 'submitted', 'in_review', 'approved', 'rejected', 'procurement'].map(s => (
            <button
              key={s}
              className={`btn btn-sm ${filter === s ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setFilter(s)}
            >
              {s ? s.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase()) : 'All'}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">⏳ Loading proposals…</div>
        ) : proposals.length === 0 ? (
          <div className="empty-state">
            <div className="icon">📋</div>
            <p>No proposals found.</p>
            {(user?.role === 'faculty' || user?.role === 'coordinator') && (
              <button className="btn btn-primary mt-4" onClick={() => navigate('/proposals/new')}>
                Submit Your First Proposal
              </button>
            )}
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th><th>Title</th><th>Type</th><th>Budget</th>
                  <th>Risk</th><th>Status</th><th>Date</th><th></th>
                </tr>
              </thead>
              <tbody>
                {proposals.map(p => (
                  <tr key={p.id} onClick={() => navigate(`/proposals/${p.id}`)} style={{ cursor: 'pointer' }}>
                    <td className="text-muted">{p.id}</td>
                    <td style={{ fontWeight: 500, maxWidth: 220 }}>
                      <div>{p.title}</div>
                      <div className="text-muted text-sm">{p.ai_intent || ''}</div>
                    </td>
                    <td><span className="chip">{eventLabel(p.event_type)}</span></td>
                    <td>{formatCurrency(p.budget)}</td>
                    <td>{riskChip(p.ai_risk_level)}</td>
                    <td>{statusBadge(p.status)}</td>
                    <td className="text-muted text-sm">{p.expected_date || formatDate(p.created_at)}</td>
                    <td>
                      {p.status === 'submitted' && user?.role === 'faculty' && (
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={e => handleDelete(p.id, e)}
                        >🗑</button>
                      )}
                    </td>
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

function riskChip(risk) {
  const map = { low: '#e8f5e9', medium: '#fff3e0', high: '#ffebee' };
  const col = { low: '#2e7d32', medium: '#e65100', high: '#c62828' };
  const r = (risk || 'low').toLowerCase();
  return (
    <span style={{ background: map[r], color: col[r], padding: '2px 8px', borderRadius: 12, fontSize: '.75rem', fontWeight: 600 }}>
      {r.charAt(0).toUpperCase() + r.slice(1)}
    </span>
  );
}
