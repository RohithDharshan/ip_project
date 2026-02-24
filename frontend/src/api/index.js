import axios from 'axios';

const API = axios.create({ baseURL: '' });

// Attach JWT token on every request
API.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// Auto-logout on 401 (only for authenticated requests, not the login call itself)
API.interceptors.response.use(
  r => r,
  err => {
    const is401 = err.response?.status === 401;
    const isLoginCall = err.config?.url?.includes('/auth/login');
    if (is401 && !isLoginCall && localStorage.getItem('token')) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────
export const login = (email, password) => {
  const form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);
  return API.post('/auth/login', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
};
export const getMe = () => API.get('/auth/me');
export const register = data => API.post('/auth/register', data);

// ── Proposals ─────────────────────────────────────────────────────────────
export const getProposals    = (params = {}) => API.get('/proposals', { params });
export const createProposal  = data          => API.post('/proposals', data);
export const getProposal     = id            => API.get(`/proposals/${id}`);
export const getWorkflow     = id            => API.get(`/proposals/${id}/workflow`);
export const getProposalAudit= id            => API.get(`/proposals/${id}/audit`);
export const getProposalAnalysis = id        => API.get(`/proposals/${id}/analysis`);
export const deleteProposal  = id            => API.delete(`/proposals/${id}`);

// ── Approvals ─────────────────────────────────────────────────────────────
export const getPending      = ()            => API.get('/approvals/pending');
export const decide          = (stepId, data)=> API.post(`/approvals/${stepId}/decide`, data);
export const getDashboard    = ()            => API.get('/approvals/dashboard');

// ── Vendors ───────────────────────────────────────────────────────────────
export const getVendors      = (params = {}) => API.get('/vendors', { params });
export const createVendor    = data          => API.post('/vendors', data);
export const getVendor       = id            => API.get(`/vendors/${id}`);
export const recommendVendors= (category)    => API.get('/vendors/recommend', { params: { category } });
export const submitQuotation = data          => API.post('/vendors/quotations', data);
export const getProcurement  = id            => API.get(`/vendors/procurement/${id}`);

// ── Analytics ─────────────────────────────────────────────────────────────
export const getOverview     = ()            => API.get('/analytics/overview');
export const getProposalStats= ()            => API.get('/analytics/proposals');
export const getApprovalStats= ()            => API.get('/analytics/approvals');
export const getVendorStats  = ()            => API.get('/analytics/vendors');
export const getAuditLog     = ()            => API.get('/analytics/audit');

export default API;
