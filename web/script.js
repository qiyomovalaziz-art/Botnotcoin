// script.js
const tg = window.Telegram.WebApp;
tg.expand();

const MAX_ENERGY = 10; // shu bilan bot.py dagi MAX_ENERGY mos bo'lsin
const tapBtn = document.getElementById("tap");
const coinsEl = document.getElementById("coins");
const energyEl = document.getElementById("energy");
const maxEnergyEl = document.getElementById("maxEnergy");
const btnProfile = document.getElementById("btnProfile");
const btnDaily = document.getElementById("btnDaily");
const btnLeader = document.getElementById("btnLeader");
const btnReferral = document.getElementById("btnReferral");

maxEnergyEl.textContent = MAX_ENERGY;

const user = tg.initDataUnsafe?.user;
const user_id = user?.id;

function showMessage(msg) {
  try {
    tg.showAlert(msg);
  } catch(e) {
    alert(msg);
  }
}

// load profile info for UI
async function loadProfile() {
  if (!user_id) {
    coinsEl.textContent = "—";
    energyEl.textContent = "—";
    return;
  }
  try {
    const res = await fetch(`/profile/${user_id}`);
    if (!res.ok) {
      coinsEl.textContent = "0";
      energyEl.textContent = MAX_ENERGY;
      return;
    }
    const data = await res.json();
    coinsEl.textContent = data.coins;
    energyEl.textContent = data.energy;
  } catch (e) {
    console.error(e);
  }
}

tapBtn.addEventListener("click", async () => {
  if (!user_id) {
    showMessage("Foydalanuvchi aniqlanmadi.");
    return;
  }
  tapBtn.disabled = true;
  try {
    const res = await fetch("/add_coin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id })
    });
    const data = await res.json();
    if (res.status === 403 && data.error === "no_energy") {
      showMessage("⚡ Energiya yo'q. Kutib turing yoki kunlik bonusni talab qiling.");
    } else if (res.ok) {
      // show animation
      animateAdd(data.added);
      coinsEl.textContent = data.coins;
      energyEl.textContent = data.energy;
    } else {
      showMessage(data.message || "Xato yuz berdi");
    }
  } catch (e) {
    console.error(e);
    showMessage("Tarmoq xatosi");
  }
  tapBtn.disabled = false;
});

function animateAdd(amount) {
  const el = document.createElement("div");
  el.className = "fly";
  el.textContent = `+${amount}`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 900);
}

// Buttons
btnProfile.addEventListener("click", async () => {
  await loadProfile();
  const uid = user_id;
  const res = await fetch(`/profile/${uid}`);
  if (res.ok) {
    const data = await res.json();
    tg.showAlert(`👤 Profil\n\n🪙 ${data.coins}  ⚡ ${data.energy}/${MAX_ENERGY}`);
  } else {
    tg.showAlert("Profil topilmadi");
  }
});

btnDaily.addEventListener("click", async () => {
  if (!user_id) return showMessage("Foydalanuvchi aniqlanmadi");
  const res = await fetch("/daily_claim", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id })
  });
  const data = await res.json();
  if (res.ok) {
    coinsEl.textContent = data.coins;
    showMessage(`🎉 Kunlik bonus olindi +${data.daily} 🪙`);
  } else {
    showMessage(data.message || "Kunlik bonusni allaqachon olgansiz");
  }
});

btnLeader.addEventListener("click", async () => {
  const res = await fetch("/leaderboard");
  const rows = await res.json();
  let text = "🏆 Leaderboard:\n\n";
  rows.forEach(r => {
    text += `${r.rank}. 👤 <${r.user_id}> — ${r.coins} 🪙\n`;
  });
  showMessage(text);
});

btnReferral.addEventListener("click", async () => {
  // referral link: t.me/<bot>?start=<your_id>
  try {
    const info = await fetch('/profile/' + user_id).then(r => r.json());
    const url = `https://t.me/${tg.initDataUnsafe?.bot?.username || 'bot'}?start=${user_id}`;
    showMessage(`🔗 Sizning referal linkingiz:\n${url}`);
  } catch (e) {
    showMessage("Referal link olinmadi");
  }
});

// initial load
loadProfile();
