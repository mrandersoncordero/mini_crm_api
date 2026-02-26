import axios from 'axios'
import type {
  Token,
  User,
  UserCreate,
  UserUpdate,
  Client,
  ClientWithLeads,
  ClientCreate,
  ClientUpdate,
  Lead,
  LeadWithDetails,
  LeadCreate,
  LeadUpdate,
  LeadStats,
  AuditLog,
} from '@/types'
import type { LeadStatus, Channel } from '@/types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

// ── Interceptor: attach JWT token ──────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Interceptor: handle 401 → redirect to login ───────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// ── Auth ───────────────────────────────────────────────
export const authApi = {
  login(username: string, password: string) {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return api.post<Token>('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  me() {
    return api.get<User>('/auth/me')
  },
}

// ── Users ──────────────────────────────────────────────
export const usersApi = {
  list(skip = 0, limit = 100) {
    return api.get<User[]>('/users/', { params: { skip, limit } })
  },
  get(id: number) {
    return api.get<User>(`/users/${id}`)
  },
  create(data: UserCreate) {
    return api.post<User>('/users/', data)
  },
  update(id: number, data: UserUpdate) {
    return api.patch<User>(`/users/${id}`, data)
  },
  delete(id: number) {
    return api.delete(`/users/${id}`)
  },
}

// ── Clients ────────────────────────────────────────────
export const clientsApi = {
  list(skip = 0, limit = 100) {
    return api.get<Client[]>('/clients/', { params: { skip, limit } })
  },
  stats() {
    return api.get<{ total: number; by_type: Record<string, number> }>('/clients/stats')
  },
  get(id: number) {
    return api.get<ClientWithLeads>(`/clients/${id}`)
  },
  create(data: ClientCreate) {
    return api.post<Client>('/clients/', data)
  },
  update(id: number, data: ClientUpdate) {
    return api.patch<Client>(`/clients/${id}`, data)
  },
  delete(id: number) {
    return api.delete(`/clients/${id}`)
  },
  search(name: string, skip = 0, limit = 100) {
    return api.get<Client[]>('/clients/search', { params: { name, skip, limit } })
  },
  advancedSearch(filters: Record<string, unknown>) {
    return api.get<Client[]>('/clients/advanced-search', { params: filters })
  },
  checkExists(params: { phone?: string; email?: string; instagram?: string }) {
    return api.get<Client | null>('/clients/check-exists', { params })
  },
}

// ── Leads ──────────────────────────────────────────────
export const leadsApi = {
  list(params?: {
    skip?: number
    limit?: number
    status?: LeadStatus
    channel?: Channel
    assigned_to_id?: number
  }) {
    return api.get<Lead[]>('/leads/', { params })
  },
  get(id: number) {
    return api.get<LeadWithDetails>(`/leads/${id}`)
  },
  create(data: LeadCreate) {
    return api.post<Lead>('/leads/', data)
  },
  update(id: number, data: LeadUpdate) {
    return api.patch<Lead>(`/leads/${id}`, data)
  },
  updateStatus(id: number, status: LeadStatus) {
    return api.patch<Lead>(`/leads/${id}/status`, { status })
  },
  assign(id: number, assignedToId: number) {
    return api.patch<Lead>(`/leads/${id}/assign`, null, {
      params: { assigned_to_id: assignedToId },
    })
  },
  delete(id: number) {
    return api.delete(`/leads/${id}`)
  },
  stats() {
    return api.get<LeadStats>('/leads/stats')
  },
  recent(hours = 24, limit = 10) {
    return api.get<Lead[]>('/leads/recent', { params: { hours, limit } })
  },
  advancedSearch(filters: Record<string, unknown>) {
    return api.get<Lead[]>('/leads/advanced-search', { params: filters })
  },
}

// ── Audit Logs ─────────────────────────────────────────
export const auditLogsApi = {
  list(skip = 0, limit = 100) {
    return api.get<AuditLog[]>('/audit-logs/', { params: { skip, limit } })
  },
}

export default api
