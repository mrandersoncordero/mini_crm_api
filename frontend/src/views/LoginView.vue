<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')

async function handleLogin() {
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    error.value = axiosErr.response?.data?.detail || 'Error al iniciar sesion'
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1>CRM</h1>
      <p class="subtitle">Inicia sesion para continuar</p>

      <Message v-if="error" severity="error" :closable="false" style="margin-bottom: 1.5rem;">
        {{ error }}
      </Message>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Usuario</label>
          <InputText
            v-model="username"
            placeholder="Ingresa tu usuario"
            style="width: 100%;"
            required
          />
        </div>

        <div class="form-group">
          <label>Contrasena</label>
          <Password
            v-model="password"
            placeholder="Ingresa tu contrasena"
            :feedback="false"
            toggle-mask
            :input-style="{ width: '100%' }"
            style="width: 100%;"
            required
          />
        </div>

        <Button
          type="submit"
          label="Iniciar Sesion"
          icon="pi pi-sign-in"
          :loading="auth.loading"
          style="width: 100%; margin-top: 0.5rem;"
        />
      </form>
    </div>
  </div>
</template>
