<template>
  <div class="bg-white p-12 rounded-b-2xl shadow-xl border-x border-b border-slate-200">
    <div class="text-center">
      <div class="bg-emerald-50 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 text-emerald-600">
        <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      </div>
      <h2 class="text-2xl font-bold text-slate-800 mb-2">Secure Residency Access</h2>
      <p class="text-slate-500 mb-8 max-w-sm mx-auto text-sm">
        Authenticate via Google to access regional Saudi records.
      </p>
      <button @click="$emit('login')"
        class="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-4 rounded-xl shadow-lg transition transform hover:-translate-y-0.5 flex items-center justify-center gap-3">
        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" class="w-6 h-6" />
        Sign in with Google
      </button>
    </div>
  </div>
</template>

<script setup>
defineEmits(['login'])
</script>
