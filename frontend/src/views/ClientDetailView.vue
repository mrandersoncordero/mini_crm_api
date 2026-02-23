<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { clientsApi } from '@/services/api'
import type { ClientWithLeads } from '@/types'
import { ClientType } from '@/types'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import ProgressSpinner from 'primevue/progressspinner'

const props = defineProps<{ id: string }>()
const router = useRouter()

const client = ref<ClientWithLeads | null>(null)
const loading = ref(false)

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-VE')
}

function clientTypeLabel(type: ClientType): string {
  return type === ClientType.NATURAL ? 'Natural' : 'Jurídico'
}

async function loadClient() {
  loading.value = true
  try {
    const response = await clientsApi.get(Number(props.id))
    client.value = response.data
  } finally {
    loading.value = false
  }
}

onMounted(loadClient)
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <ProgressSpinner />
    </div>

    <template v-else-if="client">
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
          <h1>{{ client.contact_name }}</h1>
          <span :class="['client-type-badge', client.client_type]">
            {{ clientTypeLabel(client.client_type) }}
          </span>
        </div>
      </div>

      <!-- Detail Card -->
      <div class="card" style="margin-bottom: 1.5rem">
        <div class="detail-grid">
          <div class="detail-field">
            <label>Tipo</label>
            <p>{{ clientTypeLabel(client.client_type) }}</p>
          </div>
          <div class="detail-field">
            <label>Nombre</label>
            <p>{{ client.contact_name }}</p>
          </div>
          <div class="detail-field">
            <label>Empresa</label>
            <p>{{ client.company_name ?? '—' }}</p>
          </div>
          <div class="detail-field">
            <label>Teléfono</label>
            <p>{{ client.phone }}</p>
          </div>
          <div class="detail-field">
            <label>Email</label>
            <p>{{ client.email ?? '—' }}</p>
          </div>
          <div class="detail-field">
            <label>Instagram</label>
            <p>{{ client.instagram ?? '—' }}</p>
          </div>
          <div class="detail-field">
            <label>Dirección</label>
            <p>{{ client.address }}</p>
          </div>
          <div class="detail-field">
            <label>País</label>
            <p>{{ client.country ?? '—' }}</p>
          </div>
          <div class="detail-field">
            <label>Fecha Creación</label>
            <p>{{ formatDate(client.created_at) }}</p>
          </div>
        </div>
      </div>

      <!-- Leads Table -->
      <div class="card">
        <h2 class="section-title">Leads</h2>
        <DataTable
          :value="client.leads"
          stripedRows
          paginator
          :rows="10"
          :rowsPerPageOptions="[10, 25, 50]"
          emptyMessage="No hay leads para este cliente."
        >
          <Column field="id" header="ID" sortable style="width: 5rem">
            <template #body="{ data }">
              <router-link :to="`/leads/${data.id}`" class="lead-link">
                {{ data.id }}
              </router-link>
            </template>
          </Column>
          <Column field="channel" header="Canal" sortable style="width: 9rem">
            <template #body="{ data }">
              <span :class="['channel-badge', data.channel]">{{ data.channel }}</span>
            </template>
          </Column>
          <Column field="status" header="Estado" sortable style="width: 9rem">
            <template #body="{ data }">
              <span :class="['status-badge', data.status]">{{ data.status }}</span>
            </template>
          </Column>
          <Column field="admin_notes" header="Notas Admin">
            <template #body="{ data }">
              {{ data.admin_notes ?? '—' }}
            </template>
          </Column>
          <Column field="created_at" header="Creado" sortable style="width: 9rem">
            <template #body="{ data }">
              {{ formatDate(data.created_at) }}
            </template>
          </Column>
        </DataTable>
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

.section-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 1rem;
}

.lead-link {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 500;
}

.lead-link:hover {
  text-decoration: underline;
}
</style>
