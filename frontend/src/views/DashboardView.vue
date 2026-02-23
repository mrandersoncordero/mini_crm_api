<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { leadsApi, clientsApi } from '@/services/api'
import type { LeadStats, Lead } from '@/types'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { Doughnut, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title)

const stats = ref<LeadStats | null>(null)
const recentLeads = ref<Lead[]>([])
const totalClients = ref(0)
const loading = ref(true)

onMounted(async () => {
  try {
    const [statsRes, recentRes, clientsRes] = await Promise.all([
      leadsApi.stats(),
      leadsApi.recent(24, 5),
      clientsApi.list(0, 1),
    ])
    stats.value = statsRes.data
    recentLeads.value = recentRes.data
    totalClients.value = clientsRes.data.length
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  } finally {
    loading.value = false
  }
})

const totalLeads = computed(() => {
  if (!stats.value) return 0
  return Object.values(stats.value.by_status).reduce((sum, count) => sum + count, 0)
})

const statusCount = (status: string): number => {
  return stats.value?.by_status[status] ?? 0
}

const STATUS_COLORS: Record<string, string> = {
  new: '#3B82F6',
  contacted: '#F59E0B',
  quoted: '#8B5CF6',
  closed: '#10B981',
  discarded: '#EF4444',
}

const CHANNEL_COLORS: Record<string, string> = {
  web: '#3B82F6',
  whatsapp: '#22C55E',
  instagram: '#E1306C',
  manual: '#F59E0B',
}

const statusChartData = computed(() => {
  const byStatus = stats.value?.by_status ?? {}
  const labels = Object.keys(byStatus)
  const data = Object.values(byStatus)
  const backgroundColor = labels.map((l) => STATUS_COLORS[l] ?? '#6B7280')
  return {
    labels,
    datasets: [{ data, backgroundColor }],
  }
})

const channelChartData = computed(() => {
  const byChannel = stats.value?.by_channel ?? {}
  const labels = Object.keys(byChannel)
  const data = Object.values(byChannel)
  const backgroundColor = labels.map((l) => CHANNEL_COLORS[l] ?? '#6B7280')
  return {
    labels,
    datasets: [{ label: 'Leads por canal', data, backgroundColor }],
  }
})

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' as const },
  },
}

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    y: { beginAtZero: true, ticks: { stepSize: 1 } },
  },
}

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('es-VE')
}
</script>

<template>
  <div>
    <div class="page-header">
      <h1>Dashboard</h1>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon blue">
          <i class="pi pi-users"></i>
        </div>
        <div class="stat-info">
          <span>Total Clientes: <strong>{{ totalClients }}</strong></span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon indigo">
          <i class="pi pi-chart-bar"></i>
        </div>
        <div class="stat-info">
          <span>Total Leads: <strong>{{ totalLeads }}</strong></span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon green">
          <i class="pi pi-star"></i>
        </div>
        <div class="stat-info">
          <span>Nuevos: <strong>{{ statusCount('new') }}</strong></span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon orange">
          <i class="pi pi-phone"></i>
        </div>
        <div class="stat-info">
          <span>Contactados: <strong>{{ statusCount('contacted') }}</strong></span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon purple">
          <i class="pi pi-file"></i>
        </div>
        <div class="stat-info">
          <span>Cotizados: <strong>{{ statusCount('quoted') }}</strong></span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon red">
          <i class="pi pi-check-circle"></i>
        </div>
        <div class="stat-info">
          <span>Cerrados: <strong>{{ statusCount('closed') }}</strong></span>
        </div>
      </div>
    </div>

    <!-- Charts -->
    <div class="charts-grid">
      <div class="card">
        <h3>Leads por Estado</h3>
        <div style="height: 300px">
          <Doughnut
            v-if="stats"
            :data="statusChartData"
            :options="doughnutOptions"
          />
        </div>
      </div>

      <div class="card">
        <h3>Leads por Canal</h3>
        <div style="height: 300px">
          <Bar
            v-if="stats"
            :data="channelChartData"
            :options="barOptions"
          />
        </div>
      </div>
    </div>

    <!-- Recent Leads Table -->
    <div class="card">
      <h3>Leads Recientes (últimas 24h)</h3>
      <DataTable :value="recentLeads" :loading="loading" stripedRows>
        <Column field="id" header="ID" />
        <Column field="client_id" header="Cliente ID" />
        <Column field="channel" header="Canal">
          <template #body="{ data }">
            <span :class="['channel-badge', data.channel]">{{ data.channel }}</span>
          </template>
        </Column>
        <Column field="status" header="Estado">
          <template #body="{ data }">
            <span :class="['status-badge', data.status]">{{ data.status }}</span>
          </template>
        </Column>
        <Column field="created_at" header="Fecha">
          <template #body="{ data }">
            {{ formatDate(data.created_at) }}
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
