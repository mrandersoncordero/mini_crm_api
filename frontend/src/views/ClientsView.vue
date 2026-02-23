<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { clientsApi } from '@/services/api'
import type { Client, ClientCreate, ClientUpdate } from '@/types'
import { ClientType } from '@/types'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'

const toast = useToast()
const confirm = useConfirm()

const clients = ref<Client[]>([])
const loading = ref(false)
const searchQuery = ref('')

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

// ── Data loading ──────────────────────────────────────
async function loadClients() {
  loading.value = true
  try {
    const response = searchQuery.value.trim()
      ? await clientsApi.search(searchQuery.value.trim())
      : await clientsApi.list()
    clients.value = response.data
  } catch (error) {
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

onMounted(loadClients)

// Debounced search
let searchTimeout: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadClients()
  }, 400)
})

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
    phone: client.phone,
    email: client.email ?? '',
    instagram: client.instagram ?? '',
    address: client.address,
    country: client.country ?? '',
  }
  submitted.value = false
  dialogVisible.value = true
}

function isFormValid(): boolean {
  if (!form.value.contact_name.trim()) return false
  if (!form.value.phone.trim()) return false
  if (!form.value.address.trim()) return false
  if (form.value.client_type === ClientType.JURIDICAL && !form.value.company_name?.trim()) {
    return false
  }
  return true
}

async function saveClient() {
  submitted.value = true
  if (!isFormValid()) return

  saving.value = true
  try {
    // Build payload, omitting empty optional fields
    const payload: ClientCreate = {
      client_type: form.value.client_type,
      contact_name: form.value.contact_name.trim(),
      phone: form.value.phone.trim(),
      address: form.value.address.trim(),
    }
    if (form.value.company_name?.trim()) payload.company_name = form.value.company_name.trim()
    if (form.value.email?.trim()) payload.email = form.value.email.trim()
    if (form.value.instagram?.trim()) payload.instagram = form.value.instagram.trim()
    if (form.value.country?.trim()) payload.country = form.value.country.trim()

    if (editingClient.value) {
      const updatePayload: ClientUpdate = { ...payload }
      await clientsApi.update(editingClient.value.id, updatePayload)
      toast.add({
        severity: 'success',
        summary: 'Actualizado',
        detail: 'Cliente actualizado exitosamente',
        life: 3000,
      })
    } else {
      await clientsApi.create(payload)
      toast.add({
        severity: 'success',
        summary: 'Creado',
        detail: 'Cliente creado exitosamente',
        life: 3000,
      })
    }

    dialogVisible.value = false
    await loadClients()
  } catch (error: unknown) {
    const msg =
      error instanceof Error ? error.message : 'Error al guardar el cliente'
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

function confirmDelete(client: Client) {
  confirm.require({
    message: `¿Está seguro de eliminar al cliente "${client.contact_name}"?`,
    header: 'Confirmar eliminación',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Sí, eliminar',
    rejectLabel: 'Cancelar',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await clientsApi.delete(client.id)
        toast.add({
          severity: 'success',
          summary: 'Eliminado',
          detail: 'Cliente eliminado exitosamente',
          life: 3000,
        })
        await loadClients()
      } catch {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'No se pudo eliminar el cliente',
          life: 4000,
        })
      }
    },
  })
}

function clientTypeLabel(type: ClientType): string {
  return type === ClientType.NATURAL ? 'Natural' : 'Jurídico'
}
</script>

<template>
  <div>
    <div class="page-header">
      <h1>Clientes</h1>
      <Button label="Nuevo Cliente" icon="pi pi-plus" @click="openNew" />
    </div>

    <div class="card">
      <div class="table-toolbar">
        <div class="search-group">
          <span class="p-input-icon-left search-icon">
            <i class="pi pi-search" />
            <InputText
              v-model="searchQuery"
              placeholder="Buscar clientes..."
            />
          </span>
        </div>
      </div>

      <DataTable
        :value="clients"
        :loading="loading"
        stripedRows
        paginator
        :rows="10"
        :rowsPerPageOptions="[10, 25, 50]"
        emptyMessage="No se encontraron clientes."
      >
        <Column field="id" header="ID" sortable style="width: 5rem" />
        <Column field="client_type" header="Tipo" sortable style="width: 8rem">
          <template #body="{ data }">
            <span :class="['client-type-badge', data.client_type]">
              {{ clientTypeLabel(data.client_type) }}
            </span>
          </template>
        </Column>
        <Column field="contact_name" header="Nombre Contacto" sortable>
          <template #body="{ data }">
            <router-link :to="`/clients/${data.id}`" class="client-link">
              {{ data.contact_name }}
            </router-link>
          </template>
        </Column>
        <Column field="company_name" header="Empresa" sortable />
        <Column field="phone" header="Teléfono" />
        <Column field="email" header="Email" />
        <Column field="instagram" header="Instagram" />
        <Column field="country" header="País" sortable />
        <Column header="Acciones" style="width: 10rem">
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
      :header="editingClient ? 'Editar Cliente' : 'Nuevo Cliente'"
      :modal="true"
      :style="{ width: '600px' }"
      :closable="!saving"
    >
      <div class="dialog-form">
        <div class="form-field">
          <label for="client_type">Tipo de Cliente *</label>
          <Select
            id="client_type"
            v-model="form.client_type"
            :options="clientTypeOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Seleccionar tipo"
            class="w-full"
          />
        </div>

        <div class="form-field">
          <label for="contact_name">Nombre de Contacto *</label>
          <InputText
            id="contact_name"
            v-model="form.contact_name"
            :invalid="submitted && !form.contact_name.trim()"
            class="w-full"
          />
          <small v-if="submitted && !form.contact_name.trim()" class="p-error">
            El nombre de contacto es requerido.
          </small>
        </div>

        <div class="form-field">
          <label for="company_name">
            Empresa{{ form.client_type === ClientType.JURIDICAL ? ' *' : '' }}
          </label>
          <InputText
            id="company_name"
            v-model="form.company_name"
            :invalid="submitted && form.client_type === ClientType.JURIDICAL && !form.company_name?.trim()"
            class="w-full"
          />
          <small
            v-if="submitted && form.client_type === ClientType.JURIDICAL && !form.company_name?.trim()"
            class="p-error"
          >
            La empresa es requerida para clientes jurídicos.
          </small>
        </div>

        <div class="form-field">
          <label for="phone">Teléfono *</label>
          <InputText
            id="phone"
            v-model="form.phone"
            :invalid="submitted && !form.phone.trim()"
            class="w-full"
          />
          <small v-if="submitted && !form.phone.trim()" class="p-error">
            El teléfono es requerido.
          </small>
        </div>

        <div class="form-field">
          <label for="email">Email</label>
          <InputText
            id="email"
            v-model="form.email"
            class="w-full"
          />
        </div>

        <div class="form-field">
          <label for="instagram">Instagram</label>
          <InputText
            id="instagram"
            v-model="form.instagram"
            class="w-full"
          />
        </div>

        <div class="form-field">
          <label for="address">Dirección *</label>
          <Textarea
            id="address"
            v-model="form.address"
            :invalid="submitted && !form.address.trim()"
            rows="3"
            class="w-full"
          />
          <small v-if="submitted && !form.address.trim()" class="p-error">
            La dirección es requerida.
          </small>
        </div>

        <div class="form-field">
          <label for="country">País</label>
          <InputText
            id="country"
            v-model="form.country"
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
          :label="editingClient ? 'Actualizar' : 'Crear'"
          icon="pi pi-check"
          @click="saveClient"
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

.client-link {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 500;
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
