import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'https://api.painelzap.com';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Injeta o token automaticamente em todas as requisições
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('gpfx_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
