import React, { useEffect, useState } from 'react';
import { getVendors, recommendVendors } from '../api';

const CATEGORIES = ['', 'catering', 'av_equipment', 'printing', 'logistics', 'it_services', 'venue', 'other'];

export default function VendorsPage() {
  const [vendors,  setVendors]  = useState([]);
  const [category, setCategory] = useState('');
  const [ranked,   setRanked]   = useState(null);
  const [loading,  setLoading]  = useState(true);

  const loadVendors = async () => {
    setLoading(true);
    try {
      const res = await getVendors(category ? { category } : {});
      setVendors(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadVendors(); }, [category]);

  const handleRecommend = async () => {
    const res = await recommendVendors(category || undefined);
    setRanked(res.data);
  };

  return (
    <div>
      <div className="page-header">
        <h1>🏪 Vendor Intelligence</h1>
        <p>AI-powered vendor scoring and recommendation engine</p>
      </div>

      {/* Category filter */}
      <div className="card mb-4" style={{ padding: '14px 20px' }}>
        <div className="flex-between">
          <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
            {CATEGORIES.map(c => (
              <button
                key={c}
                className={`btn btn-sm ${category === c ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setCategory(c)}
              >
                {c ? c.replace(/_/g,' ').replace(/\b\w/g, ch => ch.toUpperCase()) : 'All Categories'}
              </button>
            ))}
          </div>
          <button className="btn btn-primary btn-sm" onClick={handleRecommend}>
            🤖 AI Recommend
          </button>
        </div>
      </div>

      {/* AI Recommendation result */}
      {ranked && (
        <div className="card mb-4" style={{ borderLeft: '4px solid #00bcd4' }}>
          <div className="flex-between mb-4">
            <div className="card-title" style={{ margin: 0 }}>🏆 AI Top Recommendation</div>
            <button className="btn btn-outline btn-sm" onClick={() => setRanked(null)}>✕ Close</button>
          </div>
          <div className="alert alert-info" style={{ marginBottom: 16 }}>
            {ranked.recommendation_reason}
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Rank</th><th>Vendor</th><th>Category</th><th>Rating</th><th>AI Score</th></tr></thead>
              <tbody>
                {(ranked.ranked_vendors || []).map(v => (
                  <tr key={v.id}>
                    <td>
                      <span style={{ fontWeight: 700, color: v.recommendation_rank === 1 ? '#f59e0b' : '#6b7280' }}>
                        {v.recommendation_rank === 1 ? '🥇' : v.recommendation_rank === 2 ? '🥈' : v.recommendation_rank === 3 ? '🥉' : `#${v.recommendation_rank}`}
                      </span>
                    </td>
                    <td style={{ fontWeight: 500 }}>{v.name}</td>
                    <td><span className="chip">{v.category?.replace(/_/g,' ')}</span></td>
                    <td>{renderStars(v.rating)}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ flex: 1, height: 8, background: '#e2e8f0', borderRadius: 4 }}>
                          <div style={{ width: `${(v.ai_score || 0) * 100}%`, height: '100%', background: '#1a237e', borderRadius: 4 }} />
                        </div>
                        <span style={{ fontWeight: 700, fontSize: '.85rem' }}>{((v.ai_score || 0) * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Vendor table */}
      <div className="card">
        <div className="card-title">All Vendors ({vendors.length})</div>
        {loading ? (
          <div className="loading">⏳ Loading vendors…</div>
        ) : vendors.length === 0 ? (
          <div className="empty-state"><div className="icon">🏪</div><p>No vendors found.</p></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th><th>Category</th><th>Rating</th><th>Reliability</th>
                  <th>Price Index</th><th>Past Orders</th>
                </tr>
              </thead>
              <tbody>
                {vendors.map(v => (
                  <tr key={v.id}>
                    <td style={{ fontWeight: 500 }}>{v.name}</td>
                    <td><span className="chip">{v.category?.replace(/_/g,' ')}</span></td>
                    <td>{renderStars(v.rating)} <span className="text-muted text-sm">{v.rating}</span></td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: 60, height: 6, background: '#e2e8f0', borderRadius: 3 }}>
                          <div style={{ width: `${v.reliability * 100}%`, height: '100%', background: '#43a047', borderRadius: 3 }} />
                        </div>
                        <span className="text-sm">{(v.reliability * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td>{v.avg_price_index?.toFixed(2)}x</td>
                    <td>{v.past_orders}</td>
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

function renderStars(rating) {
  const full = Math.floor(rating);
  return (
    <span style={{ color: '#f59e0b', fontSize: '.9rem' }}>
      {'★'.repeat(full)}{'☆'.repeat(5 - full)}
    </span>
  );
}
