<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { clientsApi } from '@/services/api'
import type { Client, ClientCreate } from '@/types'
import { ClientType } from '@/types'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import DatePicker from 'primevue/datepicker'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'

const toast = useToast()
const confirm = useConfirm()

const clients = ref<Client[]>([])
const loading = ref(false)
const totalRecords = ref(0)
const lazyParams = ref({ first: 0, rows: 10 })

// Filters
const filters = ref({
  contact_name: '',
  company_name: '',
  phone: '',
  email: '',
  instagram: '',
  client_type: null as ClientType | null,
  country: '',
  date_from: null as Date | null,
  date_to: null as Date | null,
})
const showFilters = ref(false)

// Dialog state
const dialogVisible = ref(false)
const saving = ref(false)
const editingClient = ref<Client | null>(null)

// Form state
const form = ref<ClientCreate>({
  client_type: ClientType.NATURAL,
  contact_name: '',
  company_name: '',
  phone: '',
  email: '',
  instagram: '',
  address: '',
  country: '',
})

const clientTypeOptions = [
  { label: 'Natural', value: ClientType.NATURAL },
  { label: 'Jurídico', value: ClientType.JURIDICAL },
]

const submitted = ref(false)

const hasActiveFilters = computed(() => {
  return (
    filters.value.contact_name ||
    filters.value.company_name ||
    filters.value.phone ||
    filters.value.email ||
    filters.value.instagram ||
    filters.value.client_type ||
    filters.value.country ||
    filters.value.date_from ||
    filters.value.date_to
  )
})

// ── Data loading ──────────────────────────────────────
async function loadClients() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      skip: lazyParams.value.first,
      limit: lazyParams.value.rows,
    }

    if (hasActiveFilters.value) {
      if (filters.value.contact_name) params.contact_name = filters.value.contact_name
      if (filters.value.company_name) params.company_name = filters.value.company_name
      if (filters.value.phone) params.phone = filters.value.phone
      if (filters.value.email) params.email = filters.value.email
      if (filters.value.instagram) params.instagram = filters.value.instagram
      if (filters.value.client_type) params.client_type = filters.value.client_type
      if (filters.value.country) params.country = filters.value.country
      if (filters.value.date_from) params.date_from = filters.value.date_from.toISOString()
      if (filters.value.date_to) params.date_to = filters.value.date_to.toISOString()

      const response = await clientsApi.advancedSearch(params)
      clients.value = response.data
      totalRecords.value = response.data.length < lazyParams.value.rows 
        ? lazyParams.value.first + response.data.length 
        : lazyParams.value.first + lazyParams.value.rows + 1
    } else {
      const response = await clientsApi.list(lazyParams.value.first, lazyParams.value.rows)
      clients.value = response.data
      totalRecords.value = response.data.length < lazyParams.value.rows
        ? lazyParams.value.first + response.data.length
        : lazyParams.value.first + lazyParams.value.rows + 1
    }
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudieron cargar los clientes',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

function onPage(event: { first: number; rows: number }) {
  lazyParams.value.first = event.first
  lazyParams.value.rows = event.rows
  loadClients()
}

function onSort() {
  loadClients()
}

function clearFilters() {
  filters.value = {
    contact_name: '',
    company_name: '',
    phone: '',
    email: '',
    instagram: '',
    client_type: null,
    country: '',
    date_from: null,
    date_to: null,
  }
  lazyParams.value.first = 0
  loadClients()
}

onMounted(loadClients)

// ── Dialog helpers ────────────────────────────────────
function resetForm() {
  form.value = {
    client_type: ClientType.NATURAL,
    contact_name: '',
    company_name: '',
    phone: '',
    email: '',
    instagram: '',
    address: '',
    country: '',
  }
  submitted.value = false
}

function openNew() {
  editingClient.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(client: Client) {
  editingClient.value = client
  form.value = {
    client_type: client.client_type,
    contact_name: client.contact_name,
    company_name: client.company_name ?? '',
    phone: client.phone || '',
    email: client.email ?? '',
    instagram: client.instagram ?? '',
    address: client.address || '',
    country: client.country ?? '',
  }
  dialogVisible.value = true
}

async function saveClient() {
  submitted.value = true

  if (!form.value.contact_name || !form.value.phone || !form.value.address) {
    return
  }

  if (form.value.client_type === ClientType.JURIDICAL && !form.value.company_name) {
    return
  }

  saving.value = true
  try {
    if (editingClient.value) {
      await clientsApi.update(editingClient.value.id, form.value)
      toast.add({ severity: 'success', summary: 'Éxito', detail: 'Cliente actualizado', life: 3000 })
    } else {
      await clientsApi.create(form.value)
      toast.add({ severity: 'success', summary: 'Éxito', detail: 'Cliente creado', life: 3000 })
    }
    dialogVisible.value = false
    loadClients()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: err.response?.data?.detail || 'Error al guardar cliente',
      life: 3000,
    })
  } finally {
    saving.value = false
  }
}

function confirmDelete(client: Client) {
  confirm.require({
    message: `¿Eliminar cliente "${client.contact_name}"?`,
    header: 'Confirmar eliminación',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await clientsApi.delete(client.id)
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Cliente eliminado', life: 3000 })
        loadClients()
      } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo eliminar', life: 3000 })
      }
    },
  })
}
</script>

<template>
  <div class="card">
    <div class="page-header">
      <h1>Clientes</h1>
      <div class="header-actions">
        <Button
          :label="showFilters ? 'Ocultar filtros' : 'Mostrar filtros'"
          :icon="showFilters ? 'pi pi-filter-slash' : 'pi pi-filter'"
          severity="secondary"
          text
          @click="showFilters = !showFilters"
        />
        <Button label="Nuevo Cliente" icon="pi pi-plus" @click="openNew" />
      </div>
    </div>

    <!-- Filters Panel -->
    <div v-if="showFilters" class="filters-panel">
      <div class="filters-grid">
        <div class="filter-field">
          <label>Nombre de contacto</label>
          <InputText v-model="filters.contact_name" placeholder="Buscar..." @input="loadClients" />
        </div>
        <div class="filter-field">
          <label>Empresa</label>
          <InputText v-model="filters.company_name" placeholder="Buscar..." @input="loadClients" />
        </div>
        <div class="filter-field">
          <label>Teléfono</label>
          <InputText v-model="filters.phone" placeholder="Buscar..." @input="loadClients" />
        </div>
        <div class="filter-field">
          <label>Email</label>
          <InputText v-model="filters.email" placeholder="Buscar..." @input="loadClients" />
        </div>
        <div class="filter-field">
          <label>Instagram</label>
          <InputText v-model="filters.instagram" placeholder="Buscar..." @input="loadClients" />
        </div>
        <div class="filter-field">
          <label>Tipo</label>
          <Select
            v-model="filters.client_type"
            :options="clientTypeOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Todos"
            @change="loadClients"
          />
        </div>
        <div class="filter-field">
          <label>País</label>
          <InputText v-model="filters.country" placeholder="Buscar..." @input="loadClients" />
        </div>
        <div class="filter-field">
          <label>Fecha desde</label>
          <DatePicker v-model="filters.date_from" placeholder="Seleccionar" @date-select="loadClients" />
        </div>
        <div class="filter-field">
          <label>Fecha hasta</label>
          <DatePicker v-model="filters.date_to" placeholder="Seleccionar" @date-select="loadClients" />
        </div>
      </div>
      <div class="filters-actions">
        <Button label="Limpiar filtros" severity="secondary" text @click="clearFilters" />
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :value="clients"
      :loading="loading"
      :paginator="!hasActiveFilters"
      :first="lazyParams.first"
      :rows="lazyParams.rows"
      :totalRecords="totalRecords"
      :rowsPerPageOptions="[10, 25, 50]"
      lazy
      stripedRows
      removableSort
      @page="onPage"
      @sort="onSort"
    >
      <Column field="id" header="ID" sortable style="width: 60px" />
      <Column header="Tipo" style="width: 90px">
        <template #body="{ data }">
          <span :class="['type-badge', data.client_type]">
            {{ data.client_type === 'natural' ? 'Natural' : 'Jurídico' }}
          </span>
        </template>
      </Column>
      <Column field="contact_name" header="Nombre" sortable>
        <template #body="{ data }">
          <router-link :to="`/clients/${data.id}`" class="client-link">
            {{ data.contact_name }}
          </router-link>
        </template>
      </Column>
      <Column field="company_name" header="Empresa" />
      <Column field="phone" header="Teléfono" />
      <Column field="email" header="Email" />
      <Column field="country" header="País" style="width: 100px" />
      <Column header="Acciones" style="width: 120px">
        <template #body="{ data }">
          <div class="action-buttons">
            <Button icon="pi pi-pencil" text rounded severity="info" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDelete(data)" />
          </div>
        </template>
      </Column>
      <template #empty>
        <div class="empty-state">
          <i class="pi pi-users" />
          <p>No se encontraron clientes</p>
        </div>
      </template>
    </DataTable>

    <!-- Create/Edit Dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editingClient ? 'Editar Cliente' : 'Nuevo Cliente'"
      modal
      style="width: 500px"
    >
      <form @submit.prevent="saveClient" class="form-grid">
        <div class="form-field">
          <label>Tipo de cliente *</label>
          <Select
            v-model="form.client_type"
            :options="clientTypeOptions"
            optionLabel="label"
            optionValue="value"
            :invalid="submitted && !form.client_type"
          />
        </div>

        <div class="form-field">
          <label>Nombre de contacto *</label>
          <InputText v-model="form.contact_name" :invalid="submitted && !form.contact_name" />
        </div>

        <div class="form-field" v-if="form.client_type === 'juridical'">
          <label>Nombre de empresa *</label>
          <InputText v-model="form.company_name" :invalid="submitted && !form.company_name" />
        </div>

        <div class="form-field" v-else>
          <label>Nombre de empresa</label>
          <InputText v-model="form.company_name" />
        </div>

        <div class="form-field">
          <label>Teléfono *</label>
          <InputText v-model="form.phone" :invalid="submitted && !form.phone" placeholder="+58..." />
        </div>

        <div class="form-field">
          <label>Email</label>
          <InputText v-model="form.email" type="email" />
        </div>

        <div class="form-field">
          <label>Instagram</label>
          <InputText v-model="form.instagram" placeholder="@usuario" />
        </div>

        <div class="form-field full-width">
          <label>Dirección *</label>
          <Textarea v-model="form.address" :invalid="submitted && !form.address" rows="2" />
        </div>

        <div class="form-field">
          <label>País</label>
          <InputText v-model="form.country" />
        </div>
      </form>

      <template #footer>
        <Button label="Cancelar" text @click="dialogVisible = false" />
        <Button :label="editingClient ? 'Actualizar' : 'Crear'" :loading="saving" @click="saveClient" />
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

.client-link {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
}

.client-link:hover {
  text-decoration: underline;
}

.type-badge {
  display: inline-flex;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.type-badge.natural {
  background: #dbeafe;
  color: #1d4ed8;
}

.type-badge.juridical {
  background: #f3e8ff;
  color: #7c3aed;
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
