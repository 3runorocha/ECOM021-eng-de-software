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

export const imoveisAPI = {
  listar: (params) => api.get('/imoveis/imoveis/', { params }),
  buscar: (id) => api.get(`/imoveis/imoveis/${id}`),
  criar: (data) => api.post('/imoveis/imoveis/', data),
  atualizar: (id, data) => api.patch(`/imoveis/imoveis/${id}`, data),
  deletar: (id) => api.delete(`/imoveis/imoveis/${id}`),
  definirDisponibilidade: (id, disponivel) =>
    api.patch(`/imoveis/imoveis/${id}/disponibilidade`, null, { params: { disponivel } }),
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
  devolver: (id) => api.post(`/emprestimos/emprestimos/${id}/devolver`),
}

export const notificacoesAPI = {
  listar: (userId) => api.get(`/notificacoes/notificacoes/usuario/${userId}`),
  enviar: (data) => api.post('/notificacoes/notificacoes/', data),
}

export const recomendacoesAPI = {
  porUsuario: (userId) => api.get(`/recomendacao/recomendacao/${userId}`),
}

export default api