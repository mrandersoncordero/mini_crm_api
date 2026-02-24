<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usersApi } from '@/services/api'
import type { User, UserCreate, UserUpdate } from '@/types'
import { UserRole } from '@/types'
import { useAuthStore } from '@/stores/auth'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Select from 'primevue/select'
import ToggleSwitch from 'primevue/toggleswitch'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'

const toast = useToast()
const confirm = useConfirm()
const authStore = useAuthStore()

const users = ref<User[]>([])
const loading = ref(false)

// Dialog state
const dialogVisible = ref(false)
const saving = ref(false)
const editingUser = ref<User | null>(null)

// Form state
const form = ref({
  username: '',
  email: '',
  role: UserRole.SALES,
  password: '',
  is_active: true,
})

const roleOptions = [
  { label: 'Admin', value: UserRole.ADMIN },
  { label: 'Ventas', value: UserRole.SALES },
  { label: 'Administracion', value: UserRole.MANAGEMENT },
]

const submitted = ref(false)

// -- Data loading --
async function loadUsers() {
  loading.value = true
  try {
    const response = await usersApi.list()
    users.value = response.data
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudieron cargar los usuarios',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

onMounted(loadUsers)

// -- Dialog helpers --
function resetForm() {
  form.value = {
    username: '',
    email: '',
    role: UserRole.SALES,
    password: '',
    is_active: true,
  }
  submitted.value = false
}

function openNew() {
  editingUser.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(user: User) {
  editingUser.value = user
  form.value = {
    username: user.username,
    email: user.email ?? '',
    role: user.role,
    password: '',
    is_active: user.is_active,
  }
  submitted.value = false
  dialogVisible.value = true
}

function isFormValid(): boolean {
  if (!form.value.username.trim()) return false
  if (!editingUser.value && !form.value.password) return false
  return true
}

async function saveUser() {
  submitted.value = true
  if (!isFormValid()) return

  saving.value = true
  try {
    if (editingUser.value) {
      const payload: UserUpdate = {
        username: form.value.username.trim(),
        role: form.value.role,
        is_active: form.value.is_active,
      }
      if (form.value.email.trim()) payload.email = form.value.email.trim()
      if (form.value.password) payload.password = form.value.password

      await usersApi.update(editingUser.value.id, payload)
      toast.add({
        severity: 'success',
        summary: 'Actualizado',
        detail: 'Usuario actualizado exitosamente',
        life: 3000,
      })
    } else {
      const payload: UserCreate = {
        username: form.value.username.trim(),
        role: form.value.role,
        password: form.value.password,
        is_active: form.value.is_active,
      }
      if (form.value.email.trim()) payload.email = form.value.email.trim()

      await usersApi.create(payload)
      toast.add({
        severity: 'success',
        summary: 'Creado',
        detail: 'Usuario creado exitosamente',
        life: 3000,
      })
    }

    dialogVisible.value = false
    await loadUsers()
  } catch (error: unknown) {
    const msg =
      error instanceof Error ? error.message : 'Error al guardar el usuario'
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

function confirmDelete(user: User) {
  if (user.id === authStore.user?.id) {
    toast.add({
      severity: 'warn',
      summary: 'Accion no permitida',
      detail: 'No puede eliminar su propio usuario',
      life: 3000,
    })
    return
  }

  confirm.require({
    message: `Esta seguro de eliminar al usuario "${user.username}"?`,
    header: 'Confirmar eliminacion',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Si, eliminar',
    rejectLabel: 'Cancelar',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await usersApi.delete(user.id)
        toast.add({
          severity: 'success',
          summary: 'Eliminado',
          detail: 'Usuario eliminado exitosamente',
          life: 3000,
        })
        await loadUsers()
      } catch {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'No se pudo eliminar el usuario',
          life: 4000,
        })
      }
    },
  })
}

function roleLabel(role: UserRole): string {
  switch (role) {
    case UserRole.ADMIN:
      return 'Admin'
    case UserRole.SALES:
      return 'Ventas'
    case UserRole.MANAGEMENT:
      return 'Administracion'
    default:
      return role
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('es-VE')
}
</script>

<template>
  <div>
    <div class="page-header">
      <h1>Gestion de Usuarios</h1>
      <Button label="Nuevo Usuario" icon="pi pi-plus" @click="openNew" />
    </div>

    <div class="card">
      <DataTable
        :value="users"
        :loading="loading"
        stripedRows
        paginator
        :rows="10"
        :rowsPerPageOptions="[10, 25, 50]"
        emptyMessage="No se encontraron usuarios."
      >
        <Column field="id" header="ID" sortable style="width: 5rem" />
        <Column field="username" header="Usuario" sortable />
        <Column field="email" header="Email" sortable>
          <template #body="{ data }">
            {{ data.email ?? '-' }}
          </template>
        </Column>
        <Column field="role" header="Rol" sortable style="width: 9rem">
          <template #body="{ data }">
            <span :class="['role-badge', data.role]">{{ roleLabel(data.role) }}</span>
          </template>
        </Column>
        <Column field="is_active" header="Activo" sortable style="width: 7rem">
          <template #body="{ data }">
            <i
              :class="data.is_active ? 'pi pi-check-circle' : 'pi pi-times-circle'"
              :style="{ color: data.is_active ? 'var(--p-green-500, #22c55e)' : 'var(--p-red-500, #ef4444)', fontSize: '1.25rem' }"
            />
          </template>
        </Column>
        <Column field="created_at" header="Fecha Creacion" sortable style="width: 10rem">
          <template #body="{ data }">
            {{ formatDate(data.created_at) }}
          </template>
        </Column>
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
      :header="editingUser ? 'Editar Usuario' : 'Nuevo Usuario'"
      :modal="true"
      :style="{ width: '500px' }"
      :closable="!saving"
    >
      <div class="dialog-form">
        <div class="form-field">
          <label for="username">Usuario *</label>
          <InputText
            id="username"
            v-model="form.username"
            :invalid="submitted && !form.username.trim()"
            class="w-full"
          />
          <small v-if="submitted && !form.username.trim()" class="p-error">
            El nombre de usuario es requerido.
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
          <label for="role">Rol *</label>
          <Select
            id="role"
            v-model="form.role"
            :options="roleOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Seleccionar rol"
            class="w-full"
          />
        </div>

        <div class="form-field">
          <label for="password">
            {{ editingUser ? 'Contrasena' : 'Contrasena *' }}
          </label>
          <Password
            id="password"
            v-model="form.password"
            :invalid="submitted && !editingUser && !form.password"
            :placeholder="editingUser ? 'Dejar vacio para no cambiar' : ''"
            toggleMask
            :feedback="false"
            class="w-full"
            inputClass="w-full"
          />
          <small v-if="submitted && !editingUser && !form.password" class="p-error">
            La contrasena es requerida.
          </small>
        </div>

        <div class="form-field">
          <label for="is_active">Activo</label>
          <ToggleSwitch
            id="is_active"
            v-model="form.is_active"
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
          :label="editingUser ? 'Actualizar' : 'Crear'"
          icon="pi pi-check"
          @click="saveUser"
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

.role-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: capitalize;
}

.role-badge.admin {
  background-color: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.role-badge.sales {
  background-color: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.role-badge.management {
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
