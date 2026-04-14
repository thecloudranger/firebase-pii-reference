import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth'

// Firebase project: YOUR_PROJECT_ID
// Fill in apiKey, messagingSenderId, and appId from:
//   firebase apps:sdkconfig WEB YOUR_APP_ID --project YOUR_PROJECT_ID
const firebaseConfig = {
  apiKey: "PASTE_YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.firebasestorage.app",
  messagingSenderId: "PASTE_YOUR_PROJECT_NUMBER",
  appId: "PASTE_YOUR_APP_ID",
}

const app = initializeApp(firebaseConfig)
const auth = getAuth(app)

export { auth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged }
