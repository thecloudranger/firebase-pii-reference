<template>
  <div class="p-4 md:p-12 max-w-2xl mx-auto">
    <header class="bg-emerald-800 text-white p-8 rounded-t-2xl shadow-xl border-b-4 border-emerald-900">
      <h1 class="text-3xl font-black tracking-tight">KSA DATA PORTAL</h1>
      <p class="text-emerald-100 opacity-80 mt-1">Vue 3 · Sovereign Processing: Dammam (me-central2)</p>
    </header>

    <div v-if="loading" class="bg-white p-12 rounded-b-2xl shadow-xl border-x border-b border-slate-200 flex justify-center">
      <div class="animate-spin rounded-full h-10 w-10 border-t-2 border-emerald-800"></div>
    </div>

    <LoginView v-else-if="!user" @login="login" />

    <div v-else class="bg-white p-8 rounded-b-2xl shadow-xl border-x border-b border-slate-200">
      <div class="flex justify-between items-center mb-10 pb-4 border-b border-slate-100">
        <div class="flex items-center gap-4">
          <img :src="user.photoURL" class="w-12 h-12 rounded-full ring-2 ring-emerald-100" />
          <div>
            <p class="font-bold text-slate-800 text-lg leading-tight">{{ user.displayName }}</p>
            <p class="text-xs text-slate-400 font-medium">{{ user.email }}</p>
          </div>
        </div>
        <button @click="logout"
          class="px-4 py-2 text-xs font-black text-slate-400 hover:text-red-600 tracking-widest uppercase transition">
          Logout
        </button>
      </div>

      <RecordForm :token="token" @created="onRecordCreated" />
      <RecordList ref="recordListRef" :token="token" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuth } from './composables/useAuth'
import LoginView from './components/LoginView.vue'
import RecordForm from './components/RecordForm.vue'
import RecordList from './components/RecordList.vue'

const { user, token, loading, login, logout } = useAuth()
const recordListRef = ref(null)

const onRecordCreated = () => {
  recordListRef.value?.refresh()
}
</script>
