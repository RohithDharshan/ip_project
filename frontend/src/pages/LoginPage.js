import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, getMe } from '../api';
import { useAuth } from '../App';

export default function LoginPage() {
  const { setLoggedIn } = useAuth();
  const navigate        = useNavigate();
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res   = await login(email, password);
      const token = res.data.access_token;
      localStorage.setItem('token', token);
      const me    = await getMe();
      setLoggedIn(me.data, token);
      navigate('/');
    } catch (err) {
      localStorage.removeItem('token');
      setError(err.response?.data?.detail || 'Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>AgentFlow</h1>
        <p>Agentic AI Workflow Automation — PSG AI Consortium</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="Enter your institutional email"
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>
          <button
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center' }}
            disabled={loading}
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}

