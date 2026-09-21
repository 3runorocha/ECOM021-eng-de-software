import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

export const livrosAPI = {
  listar: (params) => api.get('/catalogo/livros/', { params }),
  buscar: (id) => api.get(`/catalogo/livros/${id}`),
  criar: (data) => api.post('/catalogo/livros/', data),
  atualizar: (id, data) => api.patch(`/catalogo/livros/${id}`, data),
  deletar: (id) => api.delete(`/catalogo/livros/${id}`),
}

export const usuariosAPI = {
  listar: () => api.get('/usuarios/usuarios/'),
  buscar: (id) => api.get(`/usuarios/usuarios/${id}`),
  criar: (data) => api.post('/usuarios/usuarios/registro', data),
  login: (data) => api.post('/usuarios/usuarios/login', data),
}

export const emprestimosAPI = {
  listar: (params) => api.get('/emprestimos/emprestimos/', { params }),
  buscar: (id) => api.get(`/emprestimos/emprestimos/${id}`),
  criar: (data) => api.post('/emprestimos/emprestimos/', data),
  devolver: (id) => api.patch(`/emprestimos/emprestimos/${id}/devolver`),
}

export const notificacoesAPI = {
  listar: (userId) => api.get(`/notificacoes/notificacoes/usuario/${userId}`),
  enviar: (data) => api.post('/notificacoes/notificacoes/', data),
}

export const recomendacoesAPI = {
  porUsuario: (userId) => api.get(`/recomendacao/recomendacao/${userId}`),
}

export default api