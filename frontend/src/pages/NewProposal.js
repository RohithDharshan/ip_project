import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createProposal } from '../api';

const EVENT_TYPES = [
  { value: 'workshop',      label: 'Workshop' },
  { value: 'seminar',       label: 'Seminar' },
  { value: 'conference',    label: 'Conference' },
  { value: 'guest_lecture', label: 'Guest Lecture' },
  { value: 'cultural_fest', label: 'Cultural Fest' },
  { value: 'technical_fest',label: 'Technical Fest' },
  { value: 'sports_event',  label: 'Sports Event' },
  { value: 'other',         label: 'Other' },
];

export default function NewProposal() {
  const navigate = useNavigate();
  const [form,    setForm]    = useState({
    title: '', description: '', event_type: 'workshop', budget: '',
    requirements: '', venue: '', expected_date: '', expected_attendees: 50,
  });
  const [error,   setError]   = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (field, value) => setForm(f => ({ ...f, [field]: value }));

  const handleSubmit = async e => {
    e.preventDefault();
    setError(''); setSuccess('');
    if (!form.title || !form.description || !form.budget) {
      setError('Please fill in all required fields.');
      return;
    }
    setLoading(true);
    try {
      const res = await createProposal({ ...form, budget: parseFloat(form.budget), expected_attendees: parseInt(form.expected_attendees) });
      setSuccess(`✅ Proposal #${res.data.id} submitted! AI routing: ${(res.data.ai_routing_path || []).join(' → ')}`);
      setTimeout(() => navigate(`/proposals/${res.data.id}`), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Submission failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>📝 Submit New Proposal</h1>
        <p>The AI agent will analyze and route your proposal automatically</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
        <div className="card">
          {error   && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Event Title *</label>
              <input value={form.title} onChange={e => set('title', e.target.value)} placeholder="e.g. National Workshop on Machine Learning" required />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Event Type *</label>
                <select value={form.event_type} onChange={e => set('event_type', e.target.value)}>
                  {EVENT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Budget (INR) *</label>
                <input type="number" value={form.budget} onChange={e => set('budget', e.target.value)} placeholder="e.g. 50000" min="0" required />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Expected Date</label>
                <input type="date" value={form.expected_date} onChange={e => set('expected_date', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Expected Attendees</label>
                <input type="number" value={form.expected_attendees} onChange={e => set('expected_attendees', e.target.value)} min="1" />
              </div>
            </div>

            <div className="form-group">
              <label>Venue</label>
              <input value={form.venue} onChange={e => set('venue', e.target.value)} placeholder="e.g. Main Auditorium, PSG AI Consortium" />
            </div>

            <div className="form-group">
              <label>Description *</label>
              <textarea rows={4} value={form.description} onChange={e => set('description', e.target.value)} placeholder="Describe the purpose, objectives, and expected outcomes of the event..." required />
            </div>

            <div className="form-group">
              <label>Requirements</label>
              <textarea rows={3} value={form.requirements} onChange={e => set('requirements', e.target.value)} placeholder="List items needed: e.g. Projector, sound system, catering for 100 attendees, printed materials..." />
            </div>

            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? '⏳ Submitting…' : '🚀 Submit Proposal'}
              </button>
              <button type="button" className="btn btn-outline" onClick={() => navigate('/proposals')}>Cancel</button>
            </div>
          </form>
        </div>

        {/* Info panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <div className="card-title">🤖 AI Agent Pipeline</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { icon: '📝', label: 'Proposal Understanding', desc: 'Extracts intent, risk & budget category' },
                { icon: '✅', label: 'Compliance Check',       desc: 'Validates against institutional policies' },
                { icon: '🔀', label: 'Approval Routing',       desc: 'Determines required approvers dynamically' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', gap: 10 }}>
                  <span style={{ fontSize: '1.2rem' }}>{item.icon}</span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '.85rem' }}>{item.label}</div>
                    <div className="text-muted text-sm">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="card-title">💡 Budget Guidelines</div>
            <div style={{ fontSize: '.82rem', lineHeight: 1.8 }}>
              <div><strong>Guest Lecture:</strong> Up to ₹30,000</div>
              <div><strong>Workshop:</strong> Up to ₹1,00,000</div>
              <div><strong>Conference:</strong> Up to ₹5,00,000</div>
              <div><strong>Cultural Fest:</strong> Up to ₹10,00,000</div>
              <div><strong>Technical Fest:</strong> Up to ₹8,00,000</div>
              <div><strong>Sports Event:</strong> Up to ₹3,00,000</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
