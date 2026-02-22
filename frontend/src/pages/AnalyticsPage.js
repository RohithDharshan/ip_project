import React, { useEffect, useState } from 'react';
import { getOverview, getProposalStats, getApprovalStats, getVendorStats } from '../api';
import { formatCurrency } from '../utils';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = ['#1a237e', '#00bcd4', '#43a047', '#fb8c00', '#e53935', '#7b1fa2', '#795548'];

export default function AnalyticsPage() {
  const [overview,  setOverview]  = useState(null);
  const [proposals, setProposals] = useState(null);
  const [approvals, setApprovals] = useState(null);
  const [vendors,   setVendors]   = useState(null);
  const [loading,   setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([getOverview(), getProposalStats(), getApprovalStats(), getVendorStats()])
      .then(([ov, pr, ap, ve]) => {
        setOverview(ov.data);
        setProposals(pr.data);
        setApprovals(ap.data);
        setVendors(ve.data);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">⏳ Loading analytics…</div>;

  return (
    <div>
      <div className="page-header">
        <h1>📈 Analytics</h1>
        <p>System-wide metrics and insights</p>
      </div>

      {/* KPIs */}
      <div className="stats-grid mb-6">
        <div className="stat-card"><div className="stat-value">{overview?.total_proposals}</div><div className="stat-label">Total Proposals</div></div>
        <div className="stat-card" style={{ borderColor: '#43a047' }}><div className="stat-value">{overview?.approval_rate}%</div><div className="stat-label">Approval Rate</div></div>
        <div className="stat-card" style={{ borderColor: '#00bcd4' }}><div className="stat-value">{formatCurrency(overview?.total_budget_requested)}</div><div className="stat-label">Budget Requested</div></div>
        <div className="stat-card" style={{ borderColor: '#7b1fa2' }}><div className="stat-value">{formatCurrency(overview?.total_procurement_spend)}</div><div className="stat-label">Procurement Spend</div></div>
        <div className="stat-card" style={{ borderColor: '#fb8c00' }}><div className="stat-value">{overview?.active_vendors}</div><div className="stat-label">Active Vendors</div></div>
      </div>

      <div className="grid-2 mb-6">
        {/* By Status */}
        <div className="card">
          <div className="card-title">Proposals by Status</div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={(proposals?.by_status || []).map(d => ({ name: d.status?.replace(/_/g,' '), value: d.count }))}
                cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}
              >
                {(proposals?.by_status || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* By Event Type */}
        <div className="card">
          <div className="card-title">Proposals by Event Type</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={(proposals?.by_event_type || []).map(d => ({ name: d.event_type?.replace(/_/g,' '), count: d.count }))}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#1a237e" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2 mb-6">
        {/* Approval rates by role */}
        <div className="card">
          <div className="card-title">Approval Rate by Role</div>
          {(approvals?.approval_rates || []).length === 0 ? (
            <div className="text-muted">No data yet.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {(approvals.approval_rates || []).map(r => (
                <div key={r.role}>
                  <div className="flex-between text-sm mb-4">
                    <span style={{ fontWeight: 500 }}>{r.role.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</span>
                    <span style={{ fontWeight: 700 }}>{r.approval_rate}%</span>
                  </div>
                  <div style={{ height: 8, background: '#e2e8f0', borderRadius: 4 }}>
                    <div style={{ width: `${r.approval_rate}%`, height: '100%', background: '#43a047', borderRadius: 4 }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Vendors */}
        <div className="card">
          <div className="card-title">Top Vendors by Rating</div>
          {(vendors?.top_vendors || []).length === 0 ? (
            <div className="text-muted">No vendor data.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Vendor</th><th>Category</th><th>Rating</th><th>Orders</th></tr></thead>
                <tbody>
                  {(vendors.top_vendors || []).slice(0,5).map(v => (
                    <tr key={v.id}>
                      <td style={{ fontWeight: 500 }}>{v.name}</td>
                      <td><span className="chip">{v.category?.replace(/_/g,' ')}</span></td>
                      <td style={{ color: '#f59e0b' }}>{'★'.repeat(Math.round(v.rating))}{' '}{v.rating}</td>
                      <td>{v.past_orders}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Risk and budget breakdown */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">Proposals by Risk Level</div>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={(proposals?.by_risk_level || []).map(d => ({ name: d.risk || 'unknown', value: d.count }))}
                cx="50%" cy="50%" outerRadius={65} dataKey="value"
                label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}
              >
                {(proposals?.by_risk_level || []).map((d, i) => {
                  const riskColor = { low: '#43a047', medium: '#fb8c00', high: '#e53935' };
                  return <Cell key={i} fill={riskColor[d.risk] || COLORS[i]} />;
                })}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title">Vendor Category Distribution</div>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={(vendors?.by_category || []).map(d => ({ name: d.category?.replace(/_/g,' '), value: d.count }))}
                cx="50%" cy="50%" outerRadius={65} dataKey="value"
                label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}
              >
                {(vendors?.by_category || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
