import axios from 'axios';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? `${window.location.protocol}//${window.location.host}/api`
    : 'http://localhost:8000/api');

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const auth = {
  register: (data: any) => api.post('/auth/register', data),
  login: (data: any) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};

export const profile = {
  get: () => api.get('/profile/'),
  update: (data: any) => api.put('/profile/', data),
  uploadResume: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/profile/upload-resume', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  completeness: () => api.get('/profile/completeness'),
  readiness: () => api.get('/profile/readiness'),
};

export const jobs = {
  list: (params?: any) => api.get('/jobs/', { params }),
  get: (id: number) => api.get(`/jobs/${id}`),
  create: (data: any) => api.post('/jobs/', data),
};

export const applications = {
  apply: (jobIds: number[], coverLetter?: string) => api.post('/applications/apply', { job_ids: jobIds, custom_cover_letter: coverLetter }),
  applyMatching: (data: any) => api.post('/applications/apply-matching', data),
  matchingPreview: (params?: any) => api.get('/applications/matching-preview', { params }),
  list: (params?: any) => api.get('/applications/', { params }),
  stats: () => api.get('/applications/stats'),
  reconcile: () => api.post('/applications/reconcile'),
};

export const platforms = {
  list: () => api.get('/platforms/'),
  connected: () => api.get('/platforms/connected'),
  connect: (data: any) => api.post('/platforms/connect', data),
  testConnection: (name: string, username: string, password: string) =>
    api.post(`/platforms/${name}/test-connection`, { username, password }),
  disconnect: (name: string) => api.delete(`/platforms/${name}`),
  scrape: (platformName: string, query: string, maxResults?: number, location?: string) =>
    api.post(`/platforms/scrape?platform_name=${platformName}`, { query, max_results: maxResults || 50, location: location || '' }),
  scrapeAll: () => api.post('/platforms/scrape-all'),
  digestPrefs: () => api.get('/platforms/preferences/digest'),
  setDigestPrefs: (data: any) => api.put('/platforms/preferences/digest', data),
  runDigest: () => api.post('/platforms/digest/run'),
};

export const ai = {
  coverLetter: (data: any) => api.post('/ai/cover-letter', data),
  matchScore: (data: any) => api.post('/ai/match-score', data),
  optimizeResume: (jobDesc: string) => api.post('/ai/optimize-resume', null, { params: { job_description: jobDesc } }),
};

export default api;
