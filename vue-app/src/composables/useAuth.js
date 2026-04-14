import { ref } from 'vue'
import { auth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from '../firebase'

export function useAuth() {
  const user = ref(null)
  const token = ref(null)
  const loading = ref(true)

  onAuthStateChanged(auth, async (u) => {
    if (u) {
      token.value = await u.getIdToken()
      user.value = u
    } else {
      user.value = null
      token.value = null
    }
    loading.value = false
  })

  const login = async () => {
    const provider = new GoogleAuthProvider()
    await signInWithPopup(auth, provider)
  }

  const logout = async () => {
    await signOut(auth)
  }

  return { user, token, loading, login, logout }
}
