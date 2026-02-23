<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Button from 'primevue/button'

const router = useRouter()
const auth = useAuthStore()

const sidebarOpen = ref(true)
const isMobile = ref(window.innerWidth < 768)

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebarOnMobile() {
  if (isMobile.value) {
    sidebarOpen.value = false
  }
}

function logout() {
  auth.logout()
  router.push('/login')
}

function userInitials(username: string): string {
  return username.slice(0, 2).toUpperCase()
}

if (typeof window !== 'undefined') {
  window.addEventListener('resize', () => {
    isMobile.value = window.innerWidth < 768
    if (!isMobile.value) {
      sidebarOpen.value = true
    }
  })
}
</script>

<template>
  <div class="app-layout">
    <!-- Mobile toggle button -->
    <Button
      v-if="isMobile"
      class="mobile-toggle"
      :icon="sidebarOpen ? 'pi pi-times' : 'pi pi-bars'"
      text
      rounded
      severity="secondary"
      @click="toggleSidebar"
    />

    <!-- Sidebar -->
    <aside class="sidebar" :class="{ collapsed: !sidebarOpen, 'mobile-open': sidebarOpen && isMobile }">
      <div class="sidebar-header">
        <h2>CRM</h2>
        <small>Sistema de Gestion</small>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" exact-active-class="active" @click="closeSidebarOnMobile">
          <i class="pi pi-home" />
          <span>Dashboard</span>
        </router-link>

        <router-link to="/clients" class="nav-item" @click="closeSidebarOnMobile">
          <i class="pi pi-users" />
          <span>Clientes</span>
        </router-link>

        <router-link to="/leads" class="nav-item" @click="closeSidebarOnMobile">
          <i class="pi pi-chart-line" />
          <span>Leads</span>
        </router-link>

        <router-link v-if="auth.isAdmin" to="/users" class="nav-item" @click="closeSidebarOnMobile">
          <i class="pi pi-shield" />
          <span>Usuarios</span>
        </router-link>

        <router-link v-if="auth.isAdmin" to="/audit-log" class="nav-item" @click="closeSidebarOnMobile">
          <i class="pi pi-history" />
          <span>Auditoria</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">
            {{ auth.user ? userInitials(auth.user.username) : '?' }}
          </div>
          <div class="user-details">
            <strong>{{ auth.user?.username }}</strong>
            <span>{{ auth.user?.role }}</span>
          </div>
        </div>
        <Button
          label="Cerrar Sesion"
          icon="pi pi-sign-out"
          severity="secondary"
          text
          size="small"
          @click="logout"
          style="width: 100%; color: #94a3b8;"
        />
      </div>
    </aside>

    <!-- Overlay for mobile -->
    <div 
      v-if="sidebarOpen && isMobile" 
      class="sidebar-overlay"
      @click="sidebarOpen = false"
    />

    <!-- Main Content -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.mobile-toggle {
  position: fixed;
  top: 1rem;
  left: 1rem;
  z-index: 1001;
}

.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -280px;
    top: 0;
    bottom: 0;
    z-index: 1000;
    transition: left 0.3s ease;
  }

  .sidebar.mobile-open {
    left: 0;
  }
}
</style>
