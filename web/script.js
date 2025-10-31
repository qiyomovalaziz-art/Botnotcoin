const tg = window.Telegram.WebApp;
tg.expand();

let user = tg.initDataUnsafe?.user;
let user_id = user?.id;

const tapButton = document.getElementById("tap");
const coinDisplay = document.getElementById("coins");

tapButton.addEventListener("click", () => {
  fetch("/add_coin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id }),
  })
  .then(res => res.json())
  .then(data => {
    coinDisplay.textContent = data.coins;
  });
});
