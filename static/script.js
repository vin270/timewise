// Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyA5owSMm4VFV-sEEhGrWJmf1pdvImlgH-g",
  authDomain: "timewise-f6ae9.firebaseapp.com",
  projectId: "timewise-f6ae9",
  appId: "1:694899202264:web:e4fa973a6baeadcf299fad"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// Global timer state
let isWorkSession = true;
let canLogSession = false;
let timer;
let secondsLeft = 1500; // 25 min for testing

function updateTimerDisplay() {
  const minutes = String(Math.floor(secondsLeft / 60)).padStart(2, '0');
  const seconds = String(secondsLeft % 60).padStart(2, '0');
  document.getElementById('timer-display').textContent = `${minutes}:${seconds}`;
}

function startPomodoro() {
  document.getElementById('start-button').disabled = true;

  timer = setInterval(() => {
    secondsLeft--;
    updateTimerDisplay();

    if (secondsLeft <= 0) {
      clearInterval(timer);

      if (isWorkSession) {
        isWorkSession = false;
        secondsLeft = 300; // 5 min break for testing
        document.getElementById('timer-label').textContent = 'Break Time';
        startPomodoro();
      } else {
        document.getElementById('timer-label').textContent = 'Session Complete!';
        document.getElementById('log-session-button').style.display = 'inline-block';
        document.getElementById('timer-label').textContent = 'All Done! 🎉';

        canLogSession = true;
        const btn = document.getElementById('log-session-button');
        btn.style.display = 'inline-block';
        btn.disabled = false;
      }
    }
  }, 1000);
}

//Sign in
function signIn() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();

  auth.signInWithEmailAndPassword(email, password)
    .then(creds => creds.user.getIdToken(true))  
    .then(token => {
      localStorage.setItem("idToken", token);
      document.getElementById("auth-controls").style.display = "none";
      document.getElementById("user-info").style.display = "flex";
      document.getElementById("leaderboard-container").style.display = "block";
      loadLeaderboard();
    })
    .catch(err => {
      console.error("Login error:", err);
      alert("Login failed: " + err.message);
    });
}

// Sign up
function signUp() {
  const email = document.getElementById("signupEmail").value.trim();
  const password = document.getElementById("signupPassword").value.trim();

  auth.createUserWithEmailAndPassword(email, password)
    .then(() => alert("Signup successful! Now sign in."))
    
    .catch(error => alert("Signup failed: " + error.message));
}

async function signOut() {
  const token = localStorage.getItem("idToken");
  try {
    if (token) {
      await fetch("/api/heartbeat?offline=1", {
        method: "POST",
        headers: { "Authorization": "Bearer " + token }
      });
    }
  } catch (e) {
    console.warn("offline heartbeat failed:", e);
  }

  // stop local timers
  if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null; }

  await auth.signOut();
  localStorage.clear();
  location.reload();
}


let heartbeatTimer = null;
function startHeartbeat() {
  if (heartbeatTimer) return;
  const send = async () => {
    const token = localStorage.getItem("idToken");
    if (!token) return;
    await fetch("/api/heartbeat", {
      method: "POST",
      headers: { "Authorization": "Bearer " + token }
    });
  };
  send(); 
  heartbeatTimer = setInterval(send, 30000); // every 30s
}


async function logSessionToBackend() {
  if (!canLogSession) {
    alert("You need to finish your Pomodoro + break before logging.");
    return;
  }

  const token = localStorage.getItem("idToken");
  if (!token) return alert("You must be logged in first.");

  canLogSession = false;
  const btn = document.getElementById('log-session-button');
  btn.disabled = true;

  try {
    const res = await fetch("/api/session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify({ duration: 25 })
    });

    const raw = await res.text();
    let data = {};
    if (raw) {
      try { data = JSON.parse(raw); } catch (e) {
        throw new Error("Bad JSON from server: " + raw);
      }
    }

    if (!res.ok) {
      throw new Error(data.error || (res.status + " " + res.statusText));
    }

    alert("Session logged! Points: " + data.points);
    resetTimer();

    await refreshMyPoints();
    await refreshStats();
    loadLeaderboard();

  } catch (err) {
    console.error("Failed to log session:", err);
    alert("Failed to log session: " + err.message);
  } finally {
    btn.disabled = true;
  }
}

function resetTimer() {
  isWorkSession = true;
  secondsLeft = 1500;//25mins
  updateTimerDisplay();
  document.getElementById('timer-label').textContent = 'Work Session';
  document.getElementById('start-button').disabled = false;
}

function renderLeaderboard(entries) {
  const ul = document.getElementById('leaderboard');
  ul.innerHTML = entries.map(e => {
    const status = e.online ? '🟢' : '⚪️';
    return `<li>${e.rank}. ${status} ${e.nickname} — ${e.points} pts</li>`;
  }).join('');
}


function loadLeaderboard() {
  fetch("/api/leaderboard")
    .then(r => r.json())
    .then(data => renderLeaderboard(data))
    .catch(err => console.error("Leaderboard load error:", err));
}

function refreshMyPoints() {
  const token = localStorage.getItem("idToken");
  if (!token) return;
  fetch("/api/me", { headers: { "Authorization": "Bearer " + token } })
    .then(r => r.json())
    .then(d => {
      document.getElementById("user-points").textContent = "My Points : " + d.points;
      document.getElementById("user-nickname").textContent = "My Nickname : " + d.nickname;
      document.getElementById("user-info").style.display = "flex";
      document.getElementById("user-streak").textContent = `Streak: ${s.current_streak} day(s)`;
      document.getElementById("user-online").textContent = s.online ? "Online ✅" : "Offline ⏸️";
      document.getElementById("user-last-session").textContent = s.last_session_utc
      ? `Last session: ${new Date(s.last_session_utc).toLocaleString()}`
      : "Last session: —";
    });
}

async function refreshStats() {
  const token = localStorage.getItem("idToken");
  if (!token) return;

  try {
    const res = await fetch("/api/stats", {
      headers: { "Authorization": "Bearer " + token }
    });
    const s = await res.json();
    const streakEl = document.getElementById("user-streak");
    const onlineEl = document.getElementById("user-online");
    const lastEl   = document.getElementById("user-last-session");

    if (streakEl) streakEl.textContent = `Streak: ${s.current_streak} day(s)`;
    if (onlineEl) onlineEl.textContent = s.online ? "Online ✅" : "Offline ⏸️";
    if (lastEl) {
      lastEl.textContent = s.last_session_utc
        ? `Last session: ${new Date(s.last_session_utc).toLocaleString()}`
        : "Last session: —";
    }
  } catch (e) {
    console.warn("refreshStats failed:", e);
  }
}

let meLoaded = false;

window.onload = () => {
  document.getElementById('log-session-button').style.display = 'none';
  document.getElementById('log-session-button').disabled = true;
  updateTimerDisplay();

  auth.onAuthStateChanged(user => {
    if (!user || meLoaded) return;
    meLoaded = true;

    user.getIdToken(true).then(token => {
      localStorage.setItem("idToken", token);
      document.getElementById("auth-controls").style.display = "none";
      document.getElementById("user-info").style.display = "flex";
      startHeartbeat();

      return fetch("/api/me", {
        headers: { "Authorization": "Bearer " + token }
      });
    })
    .then(r => r.json())
    .then(async data => {
      const nickEl = document.getElementById("user-nickname");
      const ptsEl  = document.getElementById("user-points");

      if (!data.nickname) {
        const nickname = prompt("Enter your nickname:");
        if (nickname) {
          await fetch("/api/setnickname", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": "Bearer " + localStorage.getItem("idToken")
            },
            body: JSON.stringify({ nickname })
          });
          nickEl.textContent = "Nickname: " + nickname;
          ptsEl.textContent  = "My Points: " + (data.points ?? 0);
        } else {
          nickEl.textContent = "Nickname: " + (user.email || "Anonymous");
          ptsEl.textContent  = "My Points: " + (data.points ?? 0);
        }
      } else {
        nickEl.textContent = "Nickname: " + data.nickname;
        ptsEl.textContent  = "My Points: " + data.points;
      }

      document.getElementById("leaderboard-container").style.display = "block";
      loadLeaderboard();
      if (!window._lbIntervalSet) {
        window._lbIntervalSet = true;
        setInterval(loadLeaderboard, 15000);
      }
      await refreshStats();
      if (!window._statsIntervalSet) {
        window._statsIntervalSet = true;
        setInterval(refreshStats, 30000);
      }
    })
    .catch(err => console.error(err));
  });
};
