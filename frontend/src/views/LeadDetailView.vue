<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { leadsApi, usersApi } from '@/services/api'
import type { LeadWithDetails, User } from '@/types'
import { LeadStatus, Channel, ClientType } from '@/types'
import Button from 'primevue/button'
import Select from 'primevue/select'
import ProgressSpinner from 'primevue/progressspinner'
import { useToast } from 'primevue/usetoast'

const props = defineProps<{ id: string }>()
const router = useRouter()
const toast = useToast()

const lead = ref<LeadWithDetails | null>(null)
const users = ref<User[]>([])
const loading = ref(false)
const updatingStatus = ref(false)
const updatingAssignment = ref(false)

const statusOptions = [
  { label: 'Nuevo', value: LeadStatus.NEW },
  { label: 'Contactado', value: LeadStatus.CONTACTED },
  { label: 'Cotizado', value: LeadStatus.QUOTED },
  { label: 'Cerrado', value: LeadStatus.CLOSED },
  { label: 'Descartado', value: LeadStatus.DISCARDED },
]

const channelLabels: Record<Channel, string> = {
  [Channel.WEB]: 'Web',
  [Channel.WHATSAPP]: 'WhatsApp',
  [Channel.INSTAGRAM]: 'Instagram',
  [Channel.MANUAL]: 'Manual',
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-VE')
}

function clientTypeLabel(type: ClientType): string {
  return type === ClientType.NATURAL ? 'Natural' : 'Jurídico'
}

async function loadLead() {
  loading.value = true
  try {
    const response = await leadsApi.get(Number(props.id))
    lead.value = response.data
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudo cargar el lead',
      life: 4000,
    })
  } finally {
    loading.value = false
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

async function onStatusChange(newStatus: LeadStatus) {
  if (!lead.value || newStatus === lead.value.status) return
  updatingStatus.value = true
  try {
    await leadsApi.updateStatus(lead.value.id, newStatus)
    toast.add({
      severity: 'success',
      summary: 'Estado actualizado',
      detail: `Lead #${lead.value.id} cambiado a "${newStatus}"`,
      life: 3000,
    })
    await loadLead()
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudo actualizar el estado',
      life: 4000,
    })
  } finally {
    updatingStatus.value = false
  }
}

async function onAssign(assignedToId: number) {
  if (!lead.value) return
  updatingAssignment.value = true
  try {
    await leadsApi.assign(lead.value.id, assignedToId)
    toast.add({
      severity: 'success',
      summary: 'Reasignado',
      detail: `Lead #${lead.value.id} reasignado exitosamente`,
      life: 3000,
    })
    await loadLead()
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudo reasignar el lead',
      life: 4000,
    })
  } finally {
    updatingAssignment.value = false
  }
}

onMounted(() => {
  loadLead()
  loadUsers()
})
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <ProgressSpinner />
    </div>

    <template v-else-if="lead">
      <!-- Header -->
      <div class="page-header">
        <div class="header-left">
          <Button
            icon="pi pi-arrow-left"
            severity="secondary"
            text
            rounded
            @click="router.back()"
          />
          <h1>Lead #{{ lead.id }}</h1>
          <span :class="['status-badge', lead.status]">{{ lead.status }}</span>
          <span :class="['channel-badge', lead.channel]">{{ channelLabels[lead.channel] }}</span>
        </div>
      </div>

      <!-- Detail Card -->
      <div class="card" style="margin-bottom: 1.5rem">
        <h2 class="section-title">Detalle del Lead</h2>
        <div class="detail-grid">
          <div class="detail-field">
            <label>Canal</label>
            <p>{{ channelLabels[lead.channel] }}</p>
          </div>
          <div class="detail-field">
            <label>Estado</label>
            <Select
              :modelValue="lead.status"
              :options="statusOptions"
              optionLabel="label"
              optionValue="value"
              :loading="updatingStatus"
              class="status-select"
              @change="(e: { value: LeadStatus }) => onStatusChange(e.value)"
            />
          </div>
          <div class="detail-field">
            <label>Notas Admin</label>
            <p>{{ lead.admin_notes ?? '—' }}</p>
          </div>
          <div class="detail-field">
            <label>Notas Ventas</label>
            <p>{{ lead.sales_notes ?? '—' }}</p>
          </div>
          <div class="detail-field">
            <label>Creado por</label>
            <p>{{ lead.created_by.username }}</p>
          </div>
          <div class="detail-field">
            <label>Asignado a</label>
            <Select
              :modelValue="lead.assigned_to_id"
              :options="users"
              optionLabel="username"
              optionValue="id"
              placeholder="Sin asignar"
              showClear
              :loading="updatingAssignment"
              class="assign-select"
              @change="(e: { value: number }) => onAssign(e.value)"
            />
          </div>
          <div class="detail-field">
            <label>Fecha Creación</label>
            <p>{{ formatDate(lead.created_at) }}</p>
          </div>
          <div v-if="lead.updated_at" class="detail-field">
            <label>Última Actualización</label>
            <p>{{ formatDate(lead.updated_at) }}</p>
          </div>
        </div>
      </div>

      <!-- Client Info Card -->
      <div class="card">
        <h2 class="section-title">Información del Cliente</h2>
        <div class="detail-grid">
          <div class="detail-field">
            <label>Nombre</label>
            <p>
              <router-link :to="`/clients/${lead.client.id}`" class="client-link">
                {{ lead.client.contact_name }}
              </router-link>
            </p>
          </div>
          <div class="detail-field">
            <label>Teléfono</label>
            <p>{{ lead.client.phone }}</p>
          </div>
          <div class="detail-field">
            <label>Email</label>
            <p>{{ lead.client.email ?? '—' }}</p>
          </div>
          <div class="detail-field">
            <label>Tipo</label>
            <p>
              <span :class="['client-type-badge', lead.client.client_type]">
                {{ clientTypeLabel(lead.client.client_type) }}
              </span>
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 1rem;
}

.status-select,
.assign-select {
  width: 100%;
  max-width: 14rem;
}

.client-link {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 600;
}

.client-link:hover {
  text-decoration: underline;
}

.client-type-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: capitalize;
}

.client-type-badge.natural {
  background-color: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.client-type-badge.juridical {
  background-color: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
}
</style>
