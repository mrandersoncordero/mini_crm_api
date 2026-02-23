import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { UserRole } from '@/types'
import { authApi } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref(false)

  // ── Getters ────────────────────────────────────────
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === UserRole.ADMIN)
  const isSales = computed(() => user.value?.role === UserRole.SALES)
  const isManagement = computed(() => user.value?.role === UserRole.MANAGEMENT)
  const fullRole = computed(() => user.value?.role ?? null)

  // ── Init from localStorage ─────────────────────────
  function init() {
    const storedToken = localStorage.getItem('access_token')
    const storedUser = localStorage.getItem('user')
    if (storedToken) {
      token.value = storedToken
    }
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
      } catch {
        user.value = null
      }
    }
  }

  // ── Login ──────────────────────────────────────────
  async function login(username: string, password: string) {
    loading.value = true
    try {
      const { data } = await authApi.login(username, password)
      token.value = data.access_token
      localStorage.setItem('access_token', data.access_token)

      const meResponse = await authApi.me()
      user.value = meResponse.data
      localStorage.setItem('user', JSON.stringify(meResponse.data))
    } finally {
      loading.value = false
    }
  }

  // ── Logout ─────────────────────────────────────────
  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  // ── Refresh user profile ──────────────────────────
  async function refreshUser() {
    if (!token.value) return
    try {
      const { data } = await authApi.me()
      user.value = data
      localStorage.setItem('user', JSON.stringify(data))
    } catch {
      logout()
    }
  }

  return {
    user,
    token,
    loading,
    isAuthenticated,
    isAdmin,
    isSales,
    isManagement,
    fullRole,
    init,
    login,
    logout,
    refreshUser,
  }
})
