<template>
  <div class="mt-12">
    <div class="flex justify-between items-center mb-6">
      <h3 class="text-xs font-black text-slate-800 tracking-widest uppercase">Verified Records</h3>
      <span class="text-[9px] font-bold text-emerald-700 bg-emerald-50 px-2 py-1 rounded-full uppercase">
        KSA Residency Verified
      </span>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-10 w-10 border-t-2 border-emerald-800"></div>
    </div>

    <p v-else-if="!items.length" class="text-slate-400 py-4 text-center">No records found in Dammam.</p>

    <ul v-else class="space-y-4">
      <li v-for="item in items" :key="item.id"
        class="border border-slate-100 rounded-lg shadow-sm overflow-hidden">
        <div class="flex justify-between p-3 bg-white">
          <span class="font-medium text-slate-700">{{ item.name }}</span>
          <span class="text-[10px] bg-slate-100 px-2 py-1 rounded font-bold uppercase">{{ item.region }}</span>
        </div>
        <DocumentUpload :item-id="item.id" :token="token" />
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import DocumentUpload from './DocumentUpload.vue'

const props = defineProps({ token: Object })

const items = ref([])
const loading = ref(true)

const { fetchItems } = useApi(props.token)

const refresh = async () => {
  loading.value = true
  try {
    items.value = await fetchItems()
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
defineExpose({ refresh })
</script>
