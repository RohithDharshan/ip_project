import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProposal, getWorkflow, getProposalAudit, getProposalAnalysis } from '../api';
import { statusBadge, riskBadge, formatCurrency, formatDate, eventLabel } from '../utils';

export default function ProposalDetail() {
  const { id }                  = useParams();
  const navigate                = useNavigate();
  const [proposal,     setProposal]     = useState(null);
  const [steps,        setSteps]        = useState([]);
  const [auditLogs,    setAuditLogs]    = useState([]);
  const [analysis,     setAnalysis]     = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
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

  // Lazy-load analysis when AI tab is first opened
  useEffect(() => {
    if (activeTab === 'ai' && !analysis && !analysisLoading) {
      setAnalysisLoading(true);
      getProposalAnalysis(id)
        .then(r => setAnalysis(r.data))
        .catch(() => setAnalysis(null))
        .finally(() => setAnalysisLoading(false));
    }
  }, [activeTab, id, analysis, analysisLoading]);

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
        <div>
          {analysisLoading && (
            <div className="card" style={{ textAlign: 'center', padding: 40 }}>
              <div style={{ fontSize: '2rem', marginBottom: 8 }}>🤖</div>
              <div className="text-muted">Running AI analysis…</div>
            </div>
          )}

          {!analysisLoading && !analysis && (
            <div className="card alert alert-error">Could not load AI analysis.</div>
          )}

          {!analysisLoading && analysis && (() => {
            const { risk, compliance, routing, ai_intent, ai_budget_cat, ai_summary } = analysis;
            const rl = risk?.risk_level || 'low';
            const riskColor = { high: '#dc2626', medium: '#d97706', low: '#16a34a' }[rl] || '#6b7280';
            const riskBg    = { high: '#fef2f2', medium: '#fffbeb', low: '#f0fdf4'  }[rl] || '#f8fafc';
            const severityColor = {
              critical: '#7f1d1d', high: '#dc2626', medium: '#d97706', low: '#16a34a'
            };
            const severityBg = {
              critical: '#fef2f2', high: '#fff1f2', medium: '#fffbeb', low: '#f0fdf4'
            };

            return (
              <>
                {/* ── Risk Level Banner ─────────────────────────────────── */}
                <div className="card mb-4" style={{ borderLeft: `5px solid ${riskColor}`, background: riskBg }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                    <div style={{ fontSize: '2.5rem' }}>
                      {rl === 'high' ? '🔴' : rl === 'medium' ? '🟡' : '🟢'}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, fontSize: '1.1rem', color: riskColor, textTransform: 'uppercase', letterSpacing: 1 }}>
                        {rl} Risk
                      </div>
                      <div className="text-sm" style={{ marginTop: 4, lineHeight: 1.6, color: '#374151' }}>
                        {ai_summary}
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 140 }}>
                      <div className="text-muted text-sm">Intent</div>
                      <div style={{ fontWeight: 600 }}>{ai_intent || '—'}</div>
                      <div className="text-muted text-sm" style={{ marginTop: 4 }}>Budget Category</div>
                      <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{ai_budget_cat || '—'}</div>
                    </div>
                  </div>
                </div>

                {/* ── Budget Analysis Bar ───────────────────────────────── */}
                {risk?.budget_analysis && (
                  <div className="card mb-4">
                    <div className="card-title">💰 Budget Analysis</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(170px,1fr))', gap: 16, marginBottom: 16 }}>
                      <div>
                        <div className="text-muted text-sm">Requested</div>
                        <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{formatCurrency(risk.budget_analysis.amount)}</div>
                      </div>
                      <div>
                        <div className="text-muted text-sm">Policy Limit</div>
                        <div style={{ fontWeight: 700 }}>{formatCurrency(risk.budget_analysis.policy_limit)}</div>
                      </div>
                      <div>
                        <div className="text-muted text-sm">Utilisation</div>
                        <div style={{ fontWeight: 700, color: risk.budget_analysis.utilisation_pct > 100 ? '#dc2626' : risk.budget_analysis.utilisation_pct > 75 ? '#d97706' : '#16a34a' }}>
                          {risk.budget_analysis.utilisation_pct}%
                        </div>
                      </div>
                      <div>
                        <div className="text-muted text-sm">Category</div>
                        <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{risk.budget_analysis.category}</div>
                      </div>
                    </div>
                    {/* Progress bar */}
                    <div style={{ background: '#e5e7eb', borderRadius: 6, height: 10, overflow: 'hidden' }}>
                      <div style={{
                        width: `${Math.min(risk.budget_analysis.utilisation_pct, 100)}%`,
                        background: risk.budget_analysis.utilisation_pct > 100 ? '#dc2626' : risk.budget_analysis.utilisation_pct > 75 ? '#d97706' : '#16a34a',
                        height: '100%', borderRadius: 6, transition: 'width .5s',
                      }} />
                    </div>
                    {risk.budget_analysis.utilisation_pct > 100 && (
                      <div className="text-sm" style={{ color: '#dc2626', marginTop: 6 }}>
                        ⚠️ Budget exceeds policy limit — requires special dispensation.
                      </div>
                    )}
                  </div>
                )}

                {/* ── Overall Mitigation ────────────────────────────────── */}
                <div className="card mb-4" style={{ borderLeft: `4px solid ${riskColor}` }}>
                  <div className="card-title">🛡️ Overall Risk Assessment &amp; Recommendation</div>
                  <p style={{ lineHeight: 1.8, color: '#374151' }}>{risk?.overall_mitigation}</p>
                </div>

                {/* ── Risk Factors ──────────────────────────────────────── */}
                <div className="card mb-4">
                  <div className="card-title">⚠️ Risk Factors &amp; Mitigation Steps</div>
                  {(risk?.risk_factors || []).length === 0 ? (
                    <div className="text-muted">No risk factors identified.</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                      {risk.risk_factors.map((f, i) => (
                        <div key={i} style={{
                          border: `1px solid ${severityColor[f.severity] || '#e2e8f0'}`,
                          borderRadius: 10,
                          overflow: 'hidden',
                        }}>
                          {/* Factor header */}
                          <div style={{
                            background: severityBg[f.severity] || '#f8fafc',
                            padding: '10px 16px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 10,
                          }}>
                            <span style={{ fontSize: '1.3rem' }}>{f.icon}</span>
                            <div style={{ flex: 1, fontWeight: 600, color: '#1f2937' }}>{f.factor}</div>
                            <span style={{
                              padding: '2px 10px',
                              borderRadius: 20,
                              fontSize: '.72rem',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              letterSpacing: .5,
                              background: severityColor[f.severity] || '#6b7280',
                              color: '#fff',
                            }}>
                              {f.severity}
                            </span>
                          </div>
                          {/* Factor body */}
                          <div style={{ padding: '12px 16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                            <div>
                              <div className="text-muted text-sm" style={{ marginBottom: 4 }}>📋 Risk Description</div>
                              <p style={{ margin: 0, lineHeight: 1.7, color: '#374151', fontSize: '.88rem' }}>{f.description}</p>
                            </div>
                            <div style={{ borderLeft: '2px solid #e2e8f0', paddingLeft: 16 }}>
                              <div className="text-muted text-sm" style={{ marginBottom: 4 }}>✅ How to Overcome</div>
                              <p style={{ margin: 0, lineHeight: 1.7, color: '#065f46', fontSize: '.88rem' }}>{f.mitigation}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* ── Compliance Check ──────────────────────────────────── */}
                <div className="card mb-4">
                  <div className="card-title">
                    {compliance?.passed ? '✅' : '❌'} Compliance Check
                    <span style={{
                      marginLeft: 10, fontSize: '.75rem', fontWeight: 700, padding: '2px 10px',
                      borderRadius: 20,
                      background: compliance?.passed ? '#d1fae5' : '#fee2e2',
                      color:      compliance?.passed ? '#065f46' : '#991b1b',
                    }}>
                      {compliance?.passed ? 'PASSED' : 'FAILED'}
                    </span>
                  </div>

                  {compliance?.issues?.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm" style={{ fontWeight: 600, color: '#dc2626', marginBottom: 8 }}>
                        🚫 Policy Violations ({compliance.issues.length})
                      </div>
                      {compliance.issues.map((issue, i) => (
                        <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 6,
                          background: '#fef2f2', padding: '8px 12px', borderRadius: 6 }}>
                          <span style={{ color: '#dc2626', flexShrink: 0 }}>✗</span>
                          <span style={{ fontSize: '.88rem', color: '#7f1d1d', lineHeight: 1.6 }}>{issue}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {compliance?.warnings?.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm" style={{ fontWeight: 600, color: '#d97706', marginBottom: 8 }}>
                        ⚠️ Warnings ({compliance.warnings.length})
                      </div>
                      {compliance.warnings.map((w, i) => (
                        <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 6,
                          background: '#fffbeb', padding: '8px 12px', borderRadius: 6 }}>
                          <span style={{ color: '#d97706', flexShrink: 0 }}>⚠</span>
                          <span style={{ fontSize: '.88rem', color: '#78350f', lineHeight: 1.6 }}>{w}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {compliance?.passed && (compliance?.warnings || []).length === 0 && (
                    <div style={{ color: '#065f46', fontSize: '.88rem', background: '#d1fae5', padding: '8px 12px', borderRadius: 6 }}>
                      ✓ Proposal passed all institutional compliance checks.
                    </div>
                  )}
                </div>

                {/* ── Routing Explanation ───────────────────────────────── */}
                <div className="card mb-4">
                  <div className="card-title">🔀 Approval Routing Rationale</div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                    {(routing?.path || []).map((role, i) => (
                      <span key={i} className="chip" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span style={{ fontWeight: 700, color: '#4f46e5', marginRight: 2 }}>{i + 1}.</span>
                        {role.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </span>
                    ))}
                  </div>
                  <p style={{ lineHeight: 1.8, color: '#374151', margin: 0, fontSize: '.9rem' }}>
                    {routing?.explanation || 'Standard approval routing applies.'}
                  </p>
                </div>
              </>
            );
          })()}
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
