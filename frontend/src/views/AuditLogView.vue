<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import ProgressSpinner from 'primevue/progressspinner'
import { auditLogsApi } from '@/services/api'
import type { AuditLog } from '@/types'
import { AuditAction } from '@/types'

const logs = ref<AuditLog[]>([])
const loading = ref(false)
const expandedRows = ref<Record<number, boolean>>({})
const totalRecords = ref(0)
const first = ref(0)
const rows = ref(20)

const actionStyles: Record<AuditAction, { background: string; color: string }> = {
  [AuditAction.CREATE]: { background: '#dcfce7', color: '#15803d' },
  [AuditAction.UPDATE]: { background: '#dbeafe', color: '#1d4ed8' },
  [AuditAction.DELETE]: { background: '#fee2e2', color: '#b91c1c' },
}

const actionLabels: Record<AuditAction, string> = {
  [AuditAction.CREATE]: 'Crear',
  [AuditAction.UPDATE]: 'Actualizar',
  [AuditAction.DELETE]: 'Eliminar',
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('es-VE') + ' ' + date.toLocaleTimeString('es-VE')
}

function formatJson(values: Record<string, unknown> | null): string {
  if (!values) return '—'
  return JSON.stringify(values, null, 2)
}

async function fetchLogs(skip: number, limit: number): Promise<void> {
  loading.value = true
  try {
    const response = await auditLogsApi.list(skip, limit)
    const data = response.data
    logs.value = data
    if (data.length < limit && skip === 0) {
      totalRecords.value = data.length
    } else if (data.length < limit) {
      totalRecords.value = skip + data.length
    } else {
      totalRecords.value = skip + limit + 1
    }
  } finally {
    loading.value = false
  }
}

function onPage(event: { first: number; rows: number }): void {
  first.value = event.first
  rows.value = event.rows
  fetchLogs(event.first, event.rows)
}

onMounted(() => {
  fetchLogs(0, rows.value)
})
</script>

<template>
  <div>
    <div class="page-header">
      <h1>Registro de Auditoria</h1>
    </div>

    <div class="card">
      <div v-if="loading && logs.length === 0" class="loading-container">
        <ProgressSpinner />
      </div>

      <DataTable
        v-else
        v-model:expandedRows="expandedRows"
        :value="logs"
        :loading="loading"
        :paginator="true"
        :rows="rows"
        :first="first"
        :totalRecords="totalRecords"
        :lazy="true"
        dataKey="id"
        @page="onPage"
        :rowsPerPageOptions="[20, 50, 100]"
      >
        <Column expander style="width: 3rem" />

        <Column field="id" header="ID" style="width: 5rem" />

        <Column field="table_name" header="Tabla" />

        <Column field="record_id" header="Registro ID" style="width: 8rem" />

        <Column field="action" header="Accion">
          <template #body="{ data }: { data: AuditLog }">
            <span
              :style="{
                padding: '0.25rem 0.75rem',
                borderRadius: '1rem',
                fontSize: '0.85rem',
                fontWeight: 600,
                background: actionStyles[data.action].background,
                color: actionStyles[data.action].color,
              }"
            >
              {{ actionLabels[data.action] }}
            </span>
          </template>
        </Column>

        <Column header="Usuario">
          <template #body="{ data }: { data: AuditLog }">
            {{ data.user.username }}
          </template>
        </Column>

        <Column header="Fecha">
          <template #body="{ data }: { data: AuditLog }">
            {{ formatDate(data.created_at) }}
          </template>
        </Column>

        <template #expansion="{ data }: { data: AuditLog }">
          <div class="expansion-content">
            <div class="expansion-panel">
              <h4>Valores Anteriores</h4>
              <pre><code>{{ formatJson(data.old_values) }}</code></pre>
            </div>
            <div class="expansion-panel">
              <h4>Valores Nuevos</h4>
              <pre><code>{{ formatJson(data.new_values) }}</code></pre>
            </div>
          </div>
        </template>

        <template #empty>
          <div style="text-align: center; padding: 2rem">
            No se encontraron registros de auditoria.
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  padding: 3rem;
}

.expansion-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  padding: 1rem 2rem;
}

.expansion-panel h4 {
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.expansion-panel pre {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 1rem;
  margin: 0;
  overflow-x: auto;
  font-size: 0.85rem;
  line-height: 1.5;
}
</style>
