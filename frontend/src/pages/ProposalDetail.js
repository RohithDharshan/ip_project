import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProposal, getWorkflow, getProposalAudit, getProcurement } from '../api';
import { statusBadge, riskBadge, formatCurrency, formatDate, eventLabel } from '../utils';

export default function ProposalDetail() {
  const { id }                  = useParams();
  const navigate                = useNavigate();
  const [proposal,     setProposal]     = useState(null);
  const [steps,        setSteps]        = useState([]);
  const [auditLogs,    setAuditLogs]    = useState([]);
  const [procurement,  setProcurement]  = useState(null);
  const [loading,      setLoading]      = useState(true);
  const [activeTab,    setActiveTab]    = useState('overview');

  useEffect(() => {
    Promise.all([getProposal(id), getWorkflow(id), getProposalAudit(id)])
      .then(([p, w, a]) => {
        setProposal(p.data);
        setSteps(w.data);
        setAuditLogs(a.data);
      })
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (proposal?.status === 'procurement' || proposal?.status === 'completed') {
      // Try to load procurement order (proposal typically has one)
      // We search by checking recent procurement orders
    }
  }, [proposal]);

  if (loading) return <div className="loading">⏳ Loading proposal…</div>;
  if (!proposal) return <div className="alert alert-error">Proposal not found.</div>;

  const TABS = [
    { id: 'overview',   label: '📋 Overview' },
    { id: 'workflow',   label: '🔀 Workflow' },
    { id: 'ai',         label: '🤖 AI Analysis' },
    { id: 'audit',      label: '🔍 Audit Trail' },
  ];

  return (
    <div>
      <div className="flex-between mb-4">
        <button className="btn btn-outline btn-sm" onClick={() => navigate('/proposals')}>← Back</button>
        {statusBadge(proposal.status)}
      </div>

      <div className="card mb-4">
        <div className="flex-between mb-4">
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700 }}>{proposal.title}</h2>
          <span style={{ color: '#6b7280', fontSize: '.85rem' }}>#{proposal.id}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(160px,1fr))', gap: 16, marginBottom: 16 }}>
          <div><div className="text-muted text-sm">Event Type</div><div><span className="chip">{eventLabel(proposal.event_type)}</span></div></div>
          <div><div className="text-muted text-sm">Budget</div><div style={{ fontWeight: 600 }}>{formatCurrency(proposal.budget)}</div></div>
          <div><div className="text-muted text-sm">Attendees</div><div style={{ fontWeight: 600 }}>{proposal.expected_attendees}</div></div>
          <div><div className="text-muted text-sm">Date</div><div style={{ fontWeight: 600 }}>{proposal.expected_date || '—'}</div></div>
          <div><div className="text-muted text-sm">Venue</div><div>{proposal.venue || '—'}</div></div>
          <div><div className="text-muted text-sm">Risk Level</div>{riskBadge(proposal.ai_risk_level)}</div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, borderBottom: '2px solid #e2e8f0', paddingBottom: 0 }}>
        {TABS.map(t => (
          <button
            key={t.id}
            className="btn btn-sm"
            onClick={() => setActiveTab(t.id)}
            style={{
              background: activeTab === t.id ? '#1a237e' : 'transparent',
              color:      activeTab === t.id ? '#fff' : '#6b7280',
              borderRadius: '6px 6px 0 0',
              border: 'none',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="card">
          <div className="form-group">
            <label>Description</label>
            <p style={{ lineHeight: 1.7 }}>{proposal.description}</p>
          </div>
          {proposal.requirements && (
            <div className="form-group">
              <label>Requirements</label>
              <p style={{ lineHeight: 1.7 }}>{proposal.requirements}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'workflow' && (
        <div className="card">
          <div className="card-title">Approval Chain</div>
          <div className="workflow-steps">
            {steps.length === 0 ? (
              <div className="text-muted">No workflow steps found.</div>
            ) : steps.map(s => (
              <div key={s.id} className="wf-step">
                <div className={`wf-dot ${s.status}`}>
                  {s.status === 'approved' ? '✓' :
                   s.status === 'rejected' ? '✗' :
                   s.status === 'pending'  ? '○' : '?'}
                </div>
                <div className="wf-content">
                  <div className="wf-role">Step {s.step_order}: {s.approver_role.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</div>
                  <div className="wf-name">{s.approver_name}</div>
                  <div>{statusBadge(s.status)}</div>
                  {s.comments && <div style={{ marginTop: 6, background: '#f8fafc', padding: '6px 10px', borderRadius: 6, fontSize: '.8rem' }}>💬 {s.comments}</div>}
                  {s.decided_at && <div className="text-sm text-muted" style={{ marginTop: 4 }}>Decided: {formatDate(s.decided_at)}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'ai' && (
        <div className="card">
          <div className="card-title">🤖 AI Agent Analysis</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div>
              <div className="text-muted text-sm mb-4">Detected Intent</div>
              <div style={{ fontWeight: 600 }}>{proposal.ai_intent || '—'}</div>
            </div>
            <div>
              <div className="text-muted text-sm mb-4">Budget Category</div>
              <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{proposal.ai_budget_cat || '—'}</div>
            </div>
            <div>
              <div className="text-muted text-sm mb-4">Risk Assessment</div>
              {riskBadge(proposal.ai_risk_level)}
            </div>
            <div>
              <div className="text-muted text-sm mb-4">Routing Path</div>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {(proposal.ai_routing_path || []).map((r, i) => (
                  <span key={i} className="chip">{r.replace(/_/g,' ')}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="card">
          <div className="card-title">🔍 Audit Trail</div>
          {auditLogs.length === 0 ? (
            <div className="text-muted">No audit entries.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Action</th><th>User</th><th>Timestamp</th><th>Details</th></tr></thead>
                <tbody>
                  {auditLogs.map(l => (
                    <tr key={l.id}>
                      <td style={{ fontWeight: 500 }}>{l.action.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</td>
                      <td>#{l.user_id}</td>
                      <td className="text-sm text-muted">{formatDate(l.timestamp)}</td>
                      <td className="text-sm text-muted">{l.details?.role || l.details?.message || ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
