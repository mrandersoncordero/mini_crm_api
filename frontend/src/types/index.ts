// ── Enums ──────────────────────────────────────────────
export enum UserRole {
  ADMIN = 'admin',
  SALES = 'sales',
  MANAGEMENT = 'management',
}

export enum ClientType {
  NATURAL = 'natural',
  JURIDICAL = 'juridical',
}

export enum Channel {
  WEB = 'web',
  WHATSAPP = 'whatsapp',
  INSTAGRAM = 'instagram',
  MANUAL = 'manual',
}

export enum LeadStatus {
  NEW = 'new',
  CONTACTED = 'contacted',
  QUOTED = 'quoted',
  CLOSED = 'closed',
  DISCARDED = 'discarded',
}

export enum AuditAction {
  CREATE = 'create',
  UPDATE = 'update',
  DELETE = 'delete',
}

// ── User ───────────────────────────────────────────────
export interface User {
  id: number
  username: string
  email: string | null
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface UserCreate {
  username: string
  email?: string
  role: UserRole
  is_active?: boolean
  password: string
}

export interface UserUpdate {
  username?: string
  email?: string
  role?: UserRole
  is_active?: boolean
  password?: string
}

// ── Client ─────────────────────────────────────────────
export interface Client {
  id: number
  client_type: ClientType
  contact_name: string
  company_name: string | null
  phone: string | null
  email: string | null
  instagram: string | null
  address: string | null
  country: string | null
  created_at: string
  updated_at: string | null
}

export interface ClientWithLeads extends Client {
  leads: Lead[]
}

export interface ClientCreate {
  client_type: ClientType
  contact_name: string
  company_name?: string
  phone?: string
  email?: string
  instagram?: string
  address?: string
  country?: string
}

export interface ClientUpdate {
  client_type?: ClientType
  contact_name?: string
  company_name?: string
  phone?: string | null
  email?: string
  instagram?: string
  address?: string | null
  country?: string
}

// ── Lead ───────────────────────────────────────────────
export interface Lead {
  id: number
  client_id: number
  channel: Channel
  status: LeadStatus
  admin_notes: string | null
  sales_notes: string | null
  assigned_to_id: number | null
  created_by_id: number
  created_at: string
  updated_at: string | null
}

export interface LeadWithDetails extends Lead {
  client: Client
  created_by: User
  assigned_to: User | null
}

export interface LeadCreate {
  client_id: number
  channel: Channel
  status?: LeadStatus
  admin_notes?: string
  sales_notes?: string
  assigned_to_id?: number
}

export interface LeadUpdate {
  client_id?: number
  channel?: Channel
  status?: LeadStatus
  admin_notes?: string
  sales_notes?: string
  assigned_to_id?: number
}

// ── Audit Log ──────────────────────────────────────────
export interface AuditLog {
  id: number
  table_name: string
  record_id: number
  action: AuditAction
  old_values: Record<string, unknown> | null
  new_values: Record<string, unknown> | null
  changed_by_id: number
  created_at: string
  user: User
}

// ── Auth ───────────────────────────────────────────────
export interface Token {
  access_token: string
  token_type: string
}

// ── Stats ──────────────────────────────────────────────
export interface LeadStats {
  by_status: Record<string, number>
  by_channel: Record<string, number>
}
