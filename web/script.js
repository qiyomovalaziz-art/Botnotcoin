const tg = window.Telegram.WebApp;
tg.expand();

const user = tg.initDataUnsafe?.user;
const user_id = user?.id;

const tapButton = document.getElementById("tap");
const coinDisplay = document.getElementById("coins");

tapButton.addEventListener("click", () => {
  tapButton.disabled = true; // vaqtincha bosilmaydi
  fetch("/add_coin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id }),
  })
    .then(res => res.json())
    .then(data => {
      animateCoin(data.added);
      coinDisplay.textContent = data.coins;
      tapButton.disabled = false;
    })
    .catch(() => {
      tapButton.disabled = false;
    });
});

function animateCoin(amount) {
  const anim = document.createElement("div");
  anim.className = "coin-fly";
  anim.textContent = `+${amount}`;
  document.body.appendChild(anim);

  setTimeout(() => anim.remove(), 1000);
}
