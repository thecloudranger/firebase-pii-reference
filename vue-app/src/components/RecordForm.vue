<template>
  <form @submit.prevent="submit">
    <label class="block text-[10px] font-black text-slate-400 mb-2 tracking-widest uppercase">
      Add PII to Firestore (Dammam)
    </label>
    <div class="flex gap-3">
      <input
        v-model="name"
        type="text"
        required
        class="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:bg-white transition outline-none shadow-inner"
        placeholder="National ID / Sensitive Data"
      />
      <button type="submit" :disabled="saving"
        class="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-8 rounded-xl font-black shadow-lg shadow-emerald-200 transition tracking-tighter">
        {{ saving ? '...' : 'SAVE' }}
      </button>
    </div>
    <p v-if="error" class="text-red-500 text-xs mt-2">{{ error }}</p>
  </form>
</template>

<script setup>
import { ref } from 'vue'
import { useApi } from '../composables/useApi'

const props = defineProps({ token: Object })
const emit = defineEmits(['created'])

const name = ref('')
const saving = ref(false)
const error = ref('')

const { createItem } = useApi(props.token)

const submit = async () => {
  saving.value = true
  error.value = ''
  try {
    await createItem(name.value)
    name.value = ''
    emit('created')
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>
