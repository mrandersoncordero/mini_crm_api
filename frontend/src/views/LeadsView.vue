<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { leadsApi, clientsApi, usersApi } from '@/services/api'
import type { Lead, LeadCreate, Client, User } from '@/types'
import { Channel, LeadStatus } from '@/types'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'

const toast = useToast()
const confirm = useConfirm()

const leads = ref<Lead[]>([])
const clients = ref<Client[]>([])
const users = ref<User[]>([])
const loading = ref(false)

// Filter state
const filterStatus = ref<LeadStatus | null>(null)
const filterChannel = ref<Channel | null>(null)

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

// ── Data loading ──────────────────────────────────────
async function loadLeads() {
  loading.value = true
  try {
    const params: {
      skip?: number
      limit?: number
      status?: LeadStatus
      channel?: Channel
    } = {
      skip: 0,
      limit: 100,
    }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterChannel.value) params.channel = filterChannel.value
    const response = await leadsApi.list(params)
    leads.value = response.data
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

async function loadClients() {
  try {
    const response = await clientsApi.list(0, 100)
    clients.value = response.data
  } catch {
    // silent — dropdown will be empty
  }
}

async function loadUsers() {
  try {
    const response = await usersApi.list(0, 100)
    users.value = response.data
  } catch {
    // silent — dropdown will be empty
  }
}

onMounted(() => {
  loadLeads()
  loadClients()
  loadUsers()
})

function applyFilters() {
  loadLeads()
}

function clearFilters() {
  filterStatus.value = null
  filterChannel.value = null
  loadLeads()
}

// ── Lookup helpers ────────────────────────────────────
function clientName(clientId: number): string {
  const client = clients.value.find((c) => c.id === clientId)
  return client ? client.contact_name : `#${clientId}`
}

function userName(userId: number | null): string {
  if (!userId) return '—'
  const user = users.value.find((u) => u.id === userId)
  return user ? user.username : `#${userId}`
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-VE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

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
    admin_notes: lead.admin_notes ?? '',
    sales_notes: lead.sales_notes ?? '',
    assigned_to_id: lead.assigned_to_id ?? undefined,
  }
  submitted.value = false
  dialogVisible.value = true
}

function isFormValid(): boolean {
  if (!form.value.client_id) return false
  if (!form.value.channel) return false
  return true
}

async function saveLead() {
  submitted.value = true
  if (!isFormValid()) return

  saving.value = true
  try {
    const payload: LeadCreate = {
      client_id: form.value.client_id,
      channel: form.value.channel,
      status: form.value.status,
    }
    if (form.value.admin_notes?.trim()) payload.admin_notes = form.value.admin_notes.trim()
    if (form.value.sales_notes?.trim()) payload.sales_notes = form.value.sales_notes.trim()
    if (form.value.assigned_to_id) payload.assigned_to_id = form.value.assigned_to_id

    if (editingLead.value) {
      await leadsApi.update(editingLead.value.id, { ...payload })
      toast.add({
        severity: 'success',
        summary: 'Actualizado',
        detail: 'Lead actualizado exitosamente',
        life: 3000,
      })
    } else {
      await leadsApi.create(payload)
      toast.add({
        severity: 'success',
        summary: 'Creado',
        detail: 'Lead creado exitosamente',
        life: 3000,
      })
    }

    dialogVisible.value = false
    await loadLeads()
  } catch (error: unknown) {
    const msg =
      error instanceof Error ? error.message : 'Error al guardar el lead'
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: msg,
      life: 4000,
    })
  } finally {
    saving.value = false
  }
}

// ── Quick status change ───────────────────────────────
async function onStatusChange(lead: Lead, newStatus: LeadStatus) {
  try {
    await leadsApi.updateStatus(lead.id, newStatus)
    lead.status = newStatus
    toast.add({
      severity: 'success',
      summary: 'Estado actualizado',
      detail: `Lead #${lead.id} cambiado a "${newStatus}"`,
      life: 3000,
    })
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudo actualizar el estado',
      life: 4000,
    })
    await loadLeads()
  }
}

// ── Delete ────────────────────────────────────────────
function confirmDelete(lead: Lead) {
  confirm.require({
    message: `¿Está seguro de eliminar el lead #${lead.id}?`,
    header: 'Confirmar eliminación',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Sí, eliminar',
    rejectLabel: 'Cancelar',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await leadsApi.delete(lead.id)
        toast.add({
          severity: 'success',
          summary: 'Eliminado',
          detail: 'Lead eliminado exitosamente',
          life: 3000,
        })
        await loadLeads()
      } catch {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'No se pudo eliminar el lead',
          life: 4000,
        })
      }
    },
  })
}
</script>

<template>
  <div>
    <div class="page-header">
      <h1>Leads</h1>
      <Button label="Nuevo Lead" icon="pi pi-plus" @click="openNew" />
    </div>

    <div class="card">
      <div class="table-toolbar">
        <div class="search-group">
          <Select
            v-model="filterStatus"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Estado"
            showClear
            class="filter-select"
            @change="applyFilters"
          />
          <Select
            v-model="filterChannel"
            :options="channelOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Canal"
            showClear
            class="filter-select"
            @change="applyFilters"
          />
          <Button
            label="Limpiar"
            severity="secondary"
            text
            icon="pi pi-filter-slash"
            @click="clearFilters"
          />
        </div>
      </div>

      <DataTable
        :value="leads"
        :loading="loading"
        stripedRows
        paginator
        :rows="10"
        :rowsPerPageOptions="[10, 25, 50]"
        emptyMessage="No se encontraron leads."
      >
        <Column field="id" header="ID" sortable style="width: 5rem">
          <template #body="{ data }">
            <router-link :to="`/leads/${data.id}`" class="lead-link">
              {{ data.id }}
            </router-link>
          </template>
        </Column>
        <Column field="client_id" header="Cliente" sortable>
          <template #body="{ data }">
            {{ clientName(data.client_id) }}
          </template>
        </Column>
        <Column field="channel" header="Canal" sortable style="width: 9rem">
          <template #body="{ data }">
            <span :class="['channel-badge', data.channel]">{{ data.channel }}</span>
          </template>
        </Column>
        <Column field="status" header="Estado" sortable style="width: 12rem">
          <template #body="{ data }">
            <Select
              :modelValue="data.status"
              :options="statusOptions"
              optionLabel="label"
              optionValue="value"
              class="status-select"
              @change="(e: { value: LeadStatus }) => onStatusChange(data, e.value)"
            />
          </template>
        </Column>
        <Column field="assigned_to_id" header="Asignado a" style="width: 9rem">
          <template #body="{ data }">
            {{ userName(data.assigned_to_id) }}
          </template>
        </Column>
        <Column field="admin_notes" header="Notas Admin">
          <template #body="{ data }">
            <span class="notes-cell">{{ data.admin_notes ?? '—' }}</span>
          </template>
        </Column>
        <Column field="created_at" header="Creado" sortable style="width: 9rem">
          <template #body="{ data }">
            {{ formatDate(data.created_at) }}
          </template>
        </Column>
        <Column header="Acciones" style="width: 8rem">
          <template #body="{ data }">
            <div class="action-buttons">
              <Button
                icon="pi pi-pencil"
                severity="info"
                text
                rounded
                @click="openEdit(data)"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                @click="confirmDelete(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Create / Edit Dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editingLead ? 'Editar Lead' : 'Nuevo Lead'"
      :modal="true"
      :style="{ width: '600px' }"
      :closable="!saving"
    >
      <div class="dialog-form">
        <div class="form-field">
          <label for="client_id">Cliente *</label>
          <Select
            id="client_id"
            v-model="form.client_id"
            :options="clients"
            optionLabel="contact_name"
            optionValue="id"
            placeholder="Seleccionar cliente"
            :invalid="submitted && !form.client_id"
            filter
            class="w-full"
          />
          <small v-if="submitted && !form.client_id" class="p-error">
            El cliente es requerido.
          </small>
        </div>

        <div class="form-field">
          <label for="channel">Canal *</label>
          <Select
            id="channel"
            v-model="form.channel"
            :options="channelOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Seleccionar canal"
            :invalid="submitted && !form.channel"
            class="w-full"
          />
          <small v-if="submitted && !form.channel" class="p-error">
            El canal es requerido.
          </small>
        </div>

        <div class="form-field">
          <label for="status">Estado</label>
          <Select
            id="status"
            v-model="form.status"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Seleccionar estado"
            class="w-full"
          />
        </div>

        <div class="form-field">
          <label for="assigned_to_id">Asignado a</label>
          <Select
            id="assigned_to_id"
            v-model="form.assigned_to_id"
            :options="users"
            optionLabel="username"
            optionValue="id"
            placeholder="Seleccionar usuario"
            showClear
            class="w-full"
          />
        </div>

        <div class="form-field">
          <label for="admin_notes">Notas Admin</label>
          <Textarea
            id="admin_notes"
            v-model="form.admin_notes"
            rows="3"
            class="w-full"
          />
        </div>

        <div class="form-field">
          <label for="sales_notes">Notas Ventas</label>
          <Textarea
            id="sales_notes"
            v-model="form.sales_notes"
            rows="3"
            class="w-full"
          />
        </div>
      </div>

      <template #footer>
        <Button
          label="Cancelar"
          severity="secondary"
          text
          @click="dialogVisible = false"
          :disabled="saving"
        />
        <Button
          :label="editingLead ? 'Actualizar' : 'Crear'"
          icon="pi pi-check"
          @click="saveLead"
          :loading="saving"
        />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.lead-link {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 600;
}

.lead-link:hover {
  text-decoration: underline;
}

.filter-select {
  min-width: 10rem;
}

.status-select {
  width: 100%;
}

.notes-cell {
  display: inline-block;
  max-width: 14rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.5rem 0;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-field label {
  font-weight: 600;
  font-size: 0.9rem;
}

.w-full {
  width: 100%;
}
</style>
