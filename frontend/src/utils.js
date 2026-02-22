import React from 'react';

// ── Currency formatter ─────────────────────────────────────────────────────
export function formatCurrency(amount) {
  if (amount == null) return '—';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
}

// ── Date formatter ─────────────────────────────────────────────────────────
export function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(dateStr));
  } catch { return dateStr; }
}

// ── Status badge ───────────────────────────────────────────────────────────
export function statusBadge(status) {
  const map = {
    draft:                { cls: 'badge-neutral', label: 'Draft' },
    submitted:            { cls: 'badge-info',    label: 'Submitted' },
    in_review:            { cls: 'badge-warning', label: 'In Review' },
    approved:             { cls: 'badge-success', label: 'Approved' },
    rejected:             { cls: 'badge-danger',  label: 'Rejected' },
    revision_requested:   { cls: 'badge-warning', label: 'Revision Needed' },
    procurement:          { cls: 'badge-purple',  label: 'Procurement' },
    completed:            { cls: 'badge-success', label: 'Completed' },
    pending:              { cls: 'badge-warning', label: 'Pending' },
    clarification_requested:{ cls: 'badge-warning', label: 'Clarification' },
  };
  const s   = String(status || '').toLowerCase();
  const cfg = map[s] || { cls: 'badge-neutral', label: s.replace(/_/g,' ') };
  return <span className={`badge ${cfg.cls}`}>{cfg.label}</span>;
}

// ── Risk badge ─────────────────────────────────────────────────────────────
export function riskBadge(risk) {
  const map = {
    low:    { cls: 'badge-success', label: '🟢 Low' },
    medium: { cls: 'badge-warning', label: '🟡 Medium' },
    high:   { cls: 'badge-danger',  label: '🔴 High' },
  };
  const cfg = map[String(risk).toLowerCase()] || { cls: 'badge-neutral', label: risk };
  return <span className={`badge ${cfg.cls}`}>{cfg.label}</span>;
}

// ── Event type label ───────────────────────────────────────────────────────
export function eventLabel(type) {
  return String(type || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
