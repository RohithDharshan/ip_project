import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, getMe } from '../api';
import { useAuth } from '../App';

const DEMO_ACCOUNTS = [
  { email: 'faculty@psgai.edu.in',      role: 'Faculty' },
  { email: 'coordinator@psgai.edu.in',  role: 'Coordinator' },
  { email: 'hod@psgai.edu.in',          role: 'HoD' },
  { email: 'principal@psgai.edu.in',    role: 'Principal' },
  { email: 'bursar@psgai.edu.in',       role: 'Bursar' },
  { email: 'admin@psgai.edu.in',        role: 'Admin' },
];

export default function LoginPage() {
  const { setLoggedIn } = useAuth();
  const navigate        = useNavigate();
  const [email,    setEmail]    = useState('faculty@psgai.edu.in');
  const [password, setPassword] = useState('Password@123');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res   = await login(email, password);
      const token = res.data.access_token;
      // Store token FIRST so the interceptor can attach it to the /me request
      localStorage.setItem('token', token);
      const me    = await getMe();
      setLoggedIn(me.data, token);
      navigate('/');
    } catch (err) {
      localStorage.removeItem('token');
      setError(err.response?.data?.detail || 'Login failed. Check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>🤖 AgentFlow</h1>
        <p>Agentic AI Workflow Automation — PSG AI Consortium</p>

        <div className="login-accounts">
          <h4>Demo Accounts (password: Password@123)</h4>
          {DEMO_ACCOUNTS.map(a => (
            <div key={a.email} style={{ cursor: 'pointer' }} onClick={() => setEmail(a.email)}>
              <span>{a.role}</span>
              <span style={{ color: '#6b7280', fontSize: '.75rem' }}>{a.email}</span>
            </div>
          ))}
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
            {loading ? 'Signing in…' : '🔐 Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
