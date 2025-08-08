// Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyA5owSMm4VFV-sEEhGrWJmf1pdvImlgH-g",
  authDomain: "timewise-f6ae9.firebaseapp.com",
  projectId: "timewise-f6ae9",
  appId: "1:694899202264:web:e4fa973a6baeadcf299fad"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// Sign-in
function signIn() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();

  auth.signInWithEmailAndPassword(email, password)
    .then(userCredential => userCredential.user.getIdToken())
    .then(token => {
      console.log("Firebase ID Token:", token);
      localStorage.setItem("idToken", token);
      alert("Login successful!");
    })
    .catch(error => {
      console.error("Login failed:", error.message);
      alert("Login failed: " + error.message);
    });
}

// Log session
function logSessionToBackend() {
  console.log("Log Session button clicked");

  const token = localStorage.getItem("idToken");
  if (!token) {
    alert("You must be logged in first.");
    return;
  }
  
  fetch("http://127.0.0.1:5000/api/session", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + token   // ← This "Bearer " prefix is important!
  },
  body: JSON.stringify({ duration: 25 })
  })

    .then(res => res.json())
    .then(data => {
      console.log("Server response:", data);
      alert("Session logged! Points: " + data.points);
    })
    .catch(err => {
      console.error("Error logging session:", err);
      alert("Failed to log session.");
    });
}

function signUp() {
  const email = document.getElementById("signupEmail").value;
  const password = document.getElementById("signupPassword").value;

  auth.createUserWithEmailAndPassword(email, password)
    .then(userCredential => {
      alert("Sign-up successful! Now log in.");
    })
    .catch(error => {
      console.error("Sign-up error:", error.message);
      alert("Sign-up failed: " + error.message);
    });
}