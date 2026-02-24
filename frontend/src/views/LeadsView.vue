<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { leadsApi, clientsApi, usersApi } from '@/services/api'
import type { Lead, LeadCreate, Client, User } from '@/types'
import { Channel, LeadStatus } from '@/types'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import DatePicker from 'primevue/datepicker'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'

const toast = useToast()
const confirm = useConfirm()

const leads = ref<Lead[]>([])
const clients = ref<Client[]>([])
const users = ref<User[]>([])
const loading = ref(false)
const totalRecords = ref(0)
const lazyParams = ref({ first: 0, rows: 10 })

// Filters
const filters = ref({
  client_id: null as number | null,
  status: null as LeadStatus | null,
  channel: null as Channel | null,
  created_by_id: null as number | null,
  assigned_to_id: null as number | null,
  date_from: null as Date | null,
  date_to: null as Date | null,
})
const showFilters = ref(false)

// Dialog state
const dialogVisible = ref(false)
const saving = ref(false)
const editingLead = ref<Lead | null>(null)
const submitted = ref(false)

// Form state
const form = ref<LeadCreate>({
  client_id: 0,
  channel: Channel.MANUAL,
  status: LeadStatus.NEW,
  admin_notes: '',
  sales_notes: '',
  assigned_to_id: undefined,
})

// Dropdown options
const channelOptions = [
  { label: 'Web', value: Channel.WEB },
  { label: 'WhatsApp', value: Channel.WHATSAPP },
  { label: 'Instagram', value: Channel.INSTAGRAM },
  { label: 'Manual', value: Channel.MANUAL },
]

const statusOptions = [
  { label: 'Nuevo', value: LeadStatus.NEW },
  { label: 'Contactado', value: LeadStatus.CONTACTED },
  { label: 'Cotizado', value: LeadStatus.QUOTED },
  { label: 'Cerrado', value: LeadStatus.CLOSED },
  { label: 'Descartado', value: LeadStatus.DISCARDED },
]

const hasActiveFilters = computed(() => {
  return (
    filters.value.client_id ||
    filters.value.status ||
    filters.value.channel ||
    filters.value.created_by_id ||
    filters.value.assigned_to_id ||
    filters.value.date_from ||
    filters.value.date_to
  )
})

// ── Data loading ──────────────────────────────────────
async function loadLeads() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      skip: lazyParams.value.first,
      limit: lazyParams.value.rows,
    }

    if (hasActiveFilters.value) {
      if (filters.value.client_id) params.client_id = filters.value.client_id
      if (filters.value.status) params.status = filters.value.status
      if (filters.value.channel) params.channel = filters.value.channel
      if (filters.value.created_by_id) params.created_by_id = filters.value.created_by_id
      if (filters.value.assigned_to_id) params.assigned_to_id = filters.value.assigned_to_id
      if (filters.value.date_from) params.date_from = filters.value.date_from.toISOString()
      if (filters.value.date_to) params.date_to = filters.value.date_to.toISOString()

      const response = await leadsApi.advancedSearch(params)
      leads.value = response.data
      totalRecords.value = response.data.length < lazyParams.value.rows
        ? lazyParams.value.first + response.data.length
        : lazyParams.value.first + lazyParams.value.rows + 1
    } else {
      const response = await leadsApi.list({ skip: lazyParams.value.first, limit: lazyParams.value.rows })
      leads.value = response.data
      totalRecords.value = response.data.length < lazyParams.value.rows
        ? lazyParams.value.first + response.data.length
        : lazyParams.value.first + lazyParams.value.rows + 1
    }
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudieron cargar los leads',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

function onPage(event: { first: number; rows: number }) {
  lazyParams.value.first = event.first
  lazyParams.value.rows = event.rows
  loadLeads()
}

function clearFilters() {
  filters.value = {
    client_id: null,
    status: null,
    channel: null,
    created_by_id: null,
    assigned_to_id: null,
    date_from: null,
    date_to: null,
  }
  lazyParams.value.first = 0
  loadLeads()
}

async function loadClients() {
  try {
    const response = await clientsApi.list(0, 100)
    clients.value = response.data
  } catch {
    // silent
  }
}

async function loadUsers() {
  try {
    const response = await usersApi.list(0, 100)
    users.value = response.data
  } catch {
    // silent
  }
}

onMounted(() => {
  loadLeads()
  loadClients()
  loadUsers()
})

// ── Dialog helpers ────────────────────────────────────
function resetForm() {
  form.value = {
    client_id: 0,
    channel: Channel.MANUAL,
    status: LeadStatus.NEW,
    admin_notes: '',
    sales_notes: '',
    assigned_to_id: undefined,
  }
  submitted.value = false
}

function openNew() {
  editingLead.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(lead: Lead) {
  editingLead.value = lead
  form.value = {
    client_id: lead.client_id,
    channel: lead.channel,
    status: lead.status,
    admin_notes: lead.admin_notes || '',
    sales_notes: lead.sales_notes || '',
    assigned_to_id: lead.assigned_to_id || undefined,
  }
  dialogVisible.value = true
}

async function saveLead() {
  submitted.value = true
  if (!form.value.client_id || !form.value.channel) {
    return
  }

  saving.value = true
  try {
    if (editingLead.value) {
      await leadsApi.update(editingLead.value.id, form.value)
      toast.add({ severity: 'success', summary: 'Éxito', detail: 'Lead actualizado', life: 3000 })
    } else {
      await leadsApi.create(form.value)
      toast.add({ severity: 'success', summary: 'Éxito', detail: 'Lead creado', life: 3000 })
    }
    dialogVisible.value = false
    loadLeads()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'Error al guardar lead',
      life: 3000,
    })
  } finally {
    saving.value = false
  }
}

function confirmDelete(lead: Lead) {
  confirm.require({
    message: `¿Eliminar lead #${lead.id}?`,
    header: 'Confirmar eliminación',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await leadsApi.delete(lead.id)
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Lead eliminado', life: 3000 })
        loadLeads()
      } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo eliminar', life: 3000 })
      }
    },
  })
}

async function onStatusChange(lead: Lead, newStatus: LeadStatus) {
  try {
    await leadsApi.updateStatus(lead.id, newStatus)
    toast.add({ severity: 'success', summary: 'Éxito', detail: 'Estado actualizado', life: 3000 })
    loadLeads()
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo actualizar', life: 3000 })
  }
}

function getClientName(clientId: number): string {
  const client = clients.value.find(c => c.id === clientId)
  return client?.contact_name || `#${clientId}`
}

function getUserName(userId: number | null): string {
  if (!userId) return '—'
  const user = users.value.find(u => u.id === userId)
  return user?.username || `#${userId}`
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-VE')
}
</script>

<template>
  <div class="card">
    <div class="page-header">
      <h1>Leads</h1>
      <div class="header-actions">
        <Button
          :label="showFilters ? 'Ocultar filtros' : 'Mostrar filtros'"
          :icon="showFilters ? 'pi pi-filter-slash' : 'pi pi-filter'"
          severity="secondary"
          text
          @click="showFilters = !showFilters"
        />
        <Button label="Nuevo Lead" icon="pi pi-plus" @click="openNew" />
      </div>
    </div>

    <!-- Filters Panel -->
    <div v-if="showFilters" class="filters-panel">
      <div class="filters-grid">
        <div class="filter-field">
          <label>Cliente</label>
          <Select
            v-model="filters.client_id"
            :options="clients"
            optionLabel="contact_name"
            optionValue="id"
            placeholder="Todos"
            filter
            @change="loadLeads"
          />
        </div>
        <div class="filter-field">
          <label>Estado</label>
          <Select
            v-model="filters.status"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Todos"
            @change="loadLeads"
          />
        </div>
        <div class="filter-field">
          <label>Canal</label>
          <Select
            v-model="filters.channel"
            :options="channelOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Todos"
            @change="loadLeads"
          />
        </div>
        <div class="filter-field">
          <label>Creado por</label>
          <Select
            v-model="filters.created_by_id"
            :options="users"
            optionLabel="username"
            optionValue="id"
            placeholder="Todos"
            @change="loadLeads"
          />
        </div>
        <div class="filter-field">
          <label>Asignado a</label>
          <Select
            v-model="filters.assigned_to_id"
            :options="users"
            optionLabel="username"
            optionValue="id"
            placeholder="Todos"
            @change="loadLeads"
          />
        </div>
        <div class="filter-field">
          <label>Fecha desde</label>
          <DatePicker v-model="filters.date_from" placeholder="Seleccionar" @date-select="loadLeads" />
        </div>
        <div class="filter-field">
          <label>Fecha hasta</label>
          <DatePicker v-model="filters.date_to" placeholder="Seleccionar" @date-select="loadLeads" />
        </div>
      </div>
      <div class="filters-actions">
        <Button label="Limpiar filtros" severity="secondary" text @click="clearFilters" />
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :value="leads"
      :loading="loading"
      :paginator="!hasActiveFilters"
      :first="lazyParams.first"
      :rows="lazyParams.rows"
      :totalRecords="totalRecords"
      :rowsPerPageOptions="[10, 25, 50]"
      lazy
      stripedRows
      @page="onPage"
    >
      <Column field="id" header="ID" style="width: 60px">
        <template #body="{ data }">
          <router-link :to="`/leads/${data.id}`" class="lead-link">
            #{{ data.id }}
          </router-link>
        </template>
      </Column>
      <Column header="Cliente" style="min-width: 150px">
        <template #body="{ data }">
          <router-link :to="`/clients/${data.client_id}`" class="client-link">
            {{ getClientName(data.client_id) }}
          </router-link>
        </template>
      </Column>
      <Column header="Canal" style="width: 100px">
        <template #body="{ data }">
          <span :class="['channel-badge', data.channel]">{{ data.channel }}</span>
        </template>
      </Column>
      <Column header="Estado" style="width: 130px">
        <template #body="{ data }">
          <Select
            :modelValue="data.status"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            size="small"
            @change="(e: { value: LeadStatus }) => onStatusChange(data, e.value)"
          >
            <template #value="{ value }">
              <span :class="['status-badge', value]">{{ value }}</span>
            </template>
          </Select>
        </template>
      </Column>
      <Column header="Asignado" style="min-width: 120px">
        <template #body="{ data }">
          {{ getUserName(data.assigned_to_id) }}
        </template>
      </Column>
      <Column field="created_at" header="Creado" style="width: 100px">
        <template #body="{ data }">
          {{ formatDate(data.created_at) }}
        </template>
      </Column>
      <Column header="Acciones" style="width: 100px">
        <template #body="{ data }">
          <div class="action-buttons">
            <Button icon="pi pi-pencil" text rounded severity="info" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDelete(data)" />
          </div>
        </template>
      </Column>
      <template #empty>
        <div class="empty-state">
          <i class="pi pi-chart-line" />
          <p>No se encontraron leads</p>
        </div>
      </template>
    </DataTable>

    <!-- Create/Edit Dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editingLead ? 'Editar Lead' : 'Nuevo Lead'"
      modal
      style="width: 500px"
    >
      <form @submit.prevent="saveLead" class="form-grid">
        <div class="form-field">
          <label>Cliente *</label>
          <Select
            v-model="form.client_id"
            :options="clients"
            optionLabel="contact_name"
            optionValue="id"
            placeholder="Seleccionar cliente"
            filter
            :invalid="submitted && !form.client_id"
          />
        </div>

        <div class="form-field">
          <label>Canal *</label>
          <Select
            v-model="form.channel"
            :options="channelOptions"
            optionLabel="label"
            optionValue="value"
            :invalid="submitted && !form.channel"
          />
        </div>

        <div class="form-field">
          <label>Estado</label>
          <Select
            v-model="form.status"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
          />
        </div>

        <div class="form-field">
          <label>Asignar a</label>
          <Select
            v-model="form.assigned_to_id"
            :options="users"
            optionLabel="username"
            optionValue="id"
            placeholder="Sin asignar"
          />
        </div>

        <div class="form-field full-width">
          <label>Notas administrativas</label>
          <Textarea v-model="form.admin_notes" rows="2" />
        </div>

        <div class="form-field full-width">
          <label>Notas de ventas</label>
          <Textarea v-model="form.sales_notes" rows="2" />
        </div>
      </form>

      <template #footer>
        <Button label="Cancelar" text @click="dialogVisible = false" />
        <Button :label="editingLead ? 'Actualizar' : 'Crear'" :loading="saving" @click="saveLead" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.filters-panel {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-field label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
}

.filters-actions {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-end;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-field label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
}

.form-field.full-width {
  grid-column: 1 / -1;
}

.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.lead-link,
.client-link {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
}

.lead-link:hover,
.client-link:hover {
  text-decoration: underline;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #94a3b8;
}

.empty-state i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .filters-grid {
    grid-template-columns: 1fr;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-field.full-width {
    grid-column: 1;
  }
}
</style>
