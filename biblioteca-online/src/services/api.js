import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_GATEWAY_URL || 'http://127.0.0.1:8000',
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

export const contratosAPI = {
  listar: (params) => api.get('/contratos/contratos/', { params }),
  buscar: (id) => api.get(`/contratos/contratos/${id}`),
  criar: (data) => api.post('/contratos/contratos/', data),
  encerrar: (id) => api.post(`/contratos/contratos/${id}/encerrar`),
}

// O serviço de notificações não tem listagem global: só por usuário. Quem
// chamava listar() sem id batia em /usuario/undefined e tomava 422.
export const notificacoesAPI = {
  listarDoUsuario: (userId) => api.get(`/notificacoes/notificacoes/usuario/${userId}`),
  enviar: (data) => api.post('/notificacoes/notificacoes/', data),
  marcarLida: (id) => api.patch(`/notificacoes/notificacoes/${id}/ler`),
  marcarTodasLidas: (userId) =>
    api.patch(`/notificacoes/notificacoes/usuario/${userId}/ler-todas`),
  varredura: () => api.post('/notificacoes/notificacoes/varredura'),
}

export const recomendacoesAPI = {
  porUsuario: (userId) => api.get(`/recomendacao/recomendacao/${userId}`),
  perfil: (userId) => api.get(`/recomendacao/recomendacao/perfil/${userId}`),
}

export const agenteAPI = {
  status: () => api.get('/agente/agente/status'),
  perguntar: (texto, inquilinoId) =>
    api.post('/agente/agente/perguntar', { texto, inquilino_id: inquilinoId }),
}

// /health e /services sao rotas livres no gateway (nao exigem token).
export const healthAPI = {
  checar: () => api.get('/health'),
}

export default api