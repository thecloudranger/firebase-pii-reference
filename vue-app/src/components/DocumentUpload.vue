<template>
  <div class="bg-slate-50 border-t border-slate-100 p-3">
    <div v-if="documents.length" class="mb-3 space-y-1">
      <div v-for="doc in documents" :key="doc.id"
        class="flex justify-between items-center text-xs text-slate-600 bg-white px-3 py-2 rounded border border-slate-100">
        <span class="truncate max-w-[60%]">{{ doc.original_filename }}</span>
        <span class="text-[10px] font-bold uppercase px-2 py-0.5 rounded"
          :class="doc.status === 'uploaded' ? 'bg-blue-50 text-blue-600' : 'bg-green-50 text-green-600'">
          {{ doc.status }}
        </span>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <label class="flex-1">
        <span class="block text-[10px] font-black text-slate-400 mb-1 tracking-widest uppercase">
          Attach Document
        </span>
        <input type="file" ref="fileInput" @change="onFileChange"
          accept=".pdf,.jpg,.jpeg,.png,.docx"
          class="block w-full text-xs text-slate-500 file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-xs file:font-bold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100" />
      </label>
      <button @click="upload" :disabled="!selectedFile || uploading"
        class="mt-5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white text-xs font-black px-4 py-2 rounded-lg transition">
        {{ uploading ? 'Uploading...' : 'Upload' }}
      </button>
    </div>

    <p v-if="error" class="text-red-500 text-xs mt-2">{{ error }}</p>
    <p v-if="success" class="text-emerald-600 text-xs mt-2 font-bold">Uploaded to Dammam (me-central2)</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'

const props = defineProps({
  itemId: String,
  token: Object,
})

const { fetchDocuments, uploadDocument } = useApi(props.token)

const documents = ref([])
const selectedFile = ref(null)
const uploading = ref(false)
const error = ref('')
const success = ref(false)
const fileInput = ref(null)

onMounted(async () => {
  documents.value = await fetchDocuments(props.itemId)
})

const onFileChange = (e) => {
  selectedFile.value = e.target.files[0] ?? null
  error.value = ''
  success.value = false
}

const upload = async () => {
  if (!selectedFile.value) return
  uploading.value = true
  error.value = ''
  success.value = false
  try {
    const result = await uploadDocument(props.itemId, selectedFile.value)
    documents.value.push({
      id: result.id,
      original_filename: selectedFile.value.name,
      status: result.status,
    })
    success.value = true
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
  } catch (e) {
    error.value = e.message
  } finally {
    uploading.value = false
  }
}
</script>
