import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPending, decide, getDashboard } from '../api';
import { formatCurrency, riskBadge } from '../utils';

export default function ApprovalsPage() {
  const navigate               = useNavigate();
  const [pending,  setPending]  = useState([]);
  const [stats,    setStats]    = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [modal,    setModal]    = useState(null); // { step }
  const [decision, setDecision] = useState('approved');
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [feedback,   setFeedback]   = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const [p, s] = await Promise.all([getPending(), getDashboard()]);
      setPending(p.data);
      setStats(s.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const openModal = step => { setModal(step); setDecision('approved'); setComments(''); setFeedback(''); };
  const closeModal = () => { setModal(null); };

  const handleDecide = async () => {
    setSubmitting(true);
    try {
      await decide(modal.id, { decision, comments });
      setFeedback(`✅ Decision recorded: ${decision}`);
      setTimeout(() => { closeModal(); load(); }, 1200);
    } catch (err) {
      setFeedback(`❌ ${err.response?.data?.detail || 'Error submitting decision.'}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>✅ Approvals</h1>
        <p>Review and decide on pending workflow steps</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="stats-grid mb-6">
          <div className="stat-card"><div className="stat-value">{stats.total}</div><div className="stat-label">Total Proposals</div></div>
          <div className="stat-card" style={{ borderColor: '#fb8c00' }}><div className="stat-value">{stats.pending}</div><div className="stat-label">Pending</div></div>
          <div className="stat-card" style={{ borderColor: '#43a047' }}><div className="stat-value">{stats.approved}</div><div className="stat-label">Approved</div></div>
          <div className="stat-card" style={{ borderColor: '#e53935' }}><div className="stat-value">{stats.rejected}</div><div className="stat-label">Rejected</div></div>
        </div>
      )}

      <div className="card">
        <div className="card-title">Pending Approvals for Your Role</div>
        {loading ? (
          <div className="loading">⏳ Loading…</div>
        ) : pending.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🎉</div>
            <p>No pending approvals at this time.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Proposal</th><th>Type</th><th>Budget</th>
                  <th>Risk</th><th>Submitted By</th><th>Step</th><th></th>
                </tr>
              </thead>
              <tbody>
                {pending.map(s => (
                  <tr key={s.id}>
                    <td>
                      <div style={{ fontWeight: 500, cursor: 'pointer' }} onClick={() => navigate(`/proposals/${s.proposal_id}`)}>
                        {s.proposal_title}
                      </div>
                      <div className="text-muted text-sm">#{s.proposal_id}</div>
                    </td>
                    <td><span className="chip">{s.proposal_event_type?.replace(/_/g,' ')}</span></td>
                    <td style={{ fontWeight: 500 }}>{formatCurrency(s.proposal_budget)}</td>
                    <td>{riskBadge(s.ai_risk_level)}</td>
                    <td>{s.submitted_by}</td>
                    <td>
                      <span className="chip">{s.approver_role.replace(/_/g,' ')}</span>
                      <div className="text-muted text-sm">Step {s.step_order}</div>
                    </td>
                    <td>
                      <button className="btn btn-primary btn-sm" onClick={() => openModal(s)}>
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Decision Modal */}
      {modal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Review: {modal.proposal_title}</h2>
            <div style={{ background: '#f8fafc', borderRadius: 8, padding: 14, marginBottom: 16, fontSize: '.875rem' }}>
              <div><strong>Budget:</strong> {formatCurrency(modal.proposal_budget)}</div>
              <div><strong>Type:</strong> {modal.proposal_event_type?.replace(/_/g,' ')}</div>
              <div><strong>Risk:</strong> {modal.ai_risk_level}</div>
              <div><strong>Submitted by:</strong> {modal.submitted_by}</div>
            </div>

            <div className="form-group">
              <label>Decision *</label>
              <div className="flex gap-2">
                {[
                  { v: 'approved',                label: '✅ Approve',      cls: 'btn-success' },
                  { v: 'rejected',                label: '❌ Reject',       cls: 'btn-danger'  },
                  { v: 'clarification_requested', label: '❓ Clarify',      cls: 'btn-warning' },
                ].map(d => (
                  <button
                    key={d.v}
                    className={`btn ${decision === d.v ? d.cls : 'btn-outline'} btn-sm`}
                    onClick={() => setDecision(d.v)}
                  >{d.label}</button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Comments</label>
              <textarea
                rows={3}
                value={comments}
                onChange={e => setComments(e.target.value)}
                placeholder="Optional remarks or conditions…"
              />
            </div>

            {feedback && (
              <div className={`alert ${feedback.startsWith('✅') ? 'alert-success' : 'alert-error'}`}>
                {feedback}
              </div>
            )}

            <div className="modal-actions">
              <button className="btn btn-outline" onClick={closeModal}>Cancel</button>
              <button
                className={`btn ${decision === 'approved' ? 'btn-success' : decision === 'rejected' ? 'btn-danger' : 'btn-warning'}`}
                onClick={handleDecide}
                disabled={submitting}
              >
                {submitting ? 'Submitting…' : 'Submit Decision'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
