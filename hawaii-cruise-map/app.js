const days = [
  { day: 1, stop: "honolulu", title: "Aloha, Honolulu", listTitle: "Honolulu, Oʻahu", subtitle: "Embarkation", time: "Depart 7:00 PM", progress: 0, island: "oahu", description: "Board Pride of America in Honolulu and sail south into the warm Pacific evening.", tags: ["Embark", "Sail-away", "Waikīkī"] },
  { day: 2, stop: "kahului", title: "Maui begins", listTitle: "Kahului, Maui", subtitle: "Arrive & stay overnight", time: "Arrive 8:00 AM", progress: 18, island: "maui", description: "A full first day on Maui, with the ship remaining in Kahului overnight.", tags: ["Road to Hāna", "Haleakalā", "Overnight"] },
  { day: 3, stop: "kahului", title: "A second Maui day", listTitle: "Kahului, Maui", subtitle: "Overnight · Day two", time: "Depart 6:00 PM", progress: 27, island: "maui", description: "Wake up in port for another day of waterfalls, upcountry views or beach time before an evening departure.", tags: ["Upcountry", "Beaches", "Depart 6 PM"] },
  { day: 4, stop: "hilo", title: "Volcano country", listTitle: "Hilo, Hawaiʻi", subtitle: "East coast of the Big Island", time: "8:00 AM – 6:00 PM", progress: 45, island: "hawaii", description: "Hilo is the lush gateway to waterfalls, gardens and Hawaiʻi Volcanoes National Park.", tags: ["Volcanoes", "Waterfalls", "Rainforest"] },
  { day: 5, stop: "kona", title: "Sunny Kona", listTitle: "Kona, Hawaiʻi", subtitle: "West coast of the Big Island", time: "7:00 AM – 5:30 PM", progress: 59, island: "hawaii", description: "The leeward coast brings coffee country, clear snorkeling water and historic Kailua Village.", tags: ["Kona coffee", "Snorkeling", "Tender port"] },
  { day: 6, stop: "nawiliwili", title: "Kauaʻi unfolds", listTitle: "Nāwiliwili, Kauaʻi", subtitle: "Arrive & stay overnight", time: "Arrive 8:00 AM", progress: 78, island: "kauai", description: "Dock on the Garden Isle for a long day among emerald valleys, rivers and canyon overlooks.", tags: ["Waimea Canyon", "Wailua River", "Overnight"] },
  { day: 7, stop: "napali", title: "The grand finale", listTitle: "Kauaʻi & Nā Pali", subtitle: "Depart, then scenic sailing", time: "Depart 2:00 PM", progress: 91, island: "kauai", description: "Leave Nāwiliwili and, conditions permitting, trace the dramatic folds of the Nā Pali Coast before returning to Honolulu the next morning.", tags: ["Nā Pali Coast", "Scenic sailing", "Return Day 8"] }
];

const dayList = document.querySelector("#dayList");
const mapCard = document.querySelector("#mapCard");
const routeProgress = document.querySelector("#routeProgress");
const progressFill = document.querySelector("#progressFill");
const progressDay = document.querySelector("#progressDay");
const progressTitle = document.querySelector("#progressTitle");
const progressCount = document.querySelector("#progressCount");
const playButton = document.querySelector("#playRoute");
let activeIndex = 0;
let playTimer = null;

dayList.innerHTML = days.map((item, index) => `
  <button class="day-item${index === 0 ? " active" : ""}" type="button" data-day="${index}">
    <span class="day-number">${String(item.day).padStart(2, "0")}</span>
    <span class="day-copy"><strong>${item.listTitle}</strong><small>${item.subtitle}</small></span>
    <span class="day-time">${item.time}</span>
  </button>
`).join("");

function selectDay(index, options = {}) {
  activeIndex = (index + days.length) % days.length;
  const item = days[activeIndex];
  document.querySelectorAll(".day-item").forEach((el, i) => el.classList.toggle("active", i === activeIndex));
  document.querySelectorAll(".port-marker").forEach(el => el.classList.toggle("active", el.dataset.stop === item.stop));
  document.querySelectorAll(".island").forEach(el => el.classList.toggle("active", el.dataset.island === item.island));
  routeProgress.style.strokeDashoffset = 100 - item.progress;
  progressFill.style.width = `${((activeIndex + 1) / days.length) * 100}%`;
  progressDay.textContent = `DAY ${item.day}`;
  progressTitle.textContent = item.title;
  progressCount.textContent = `${String(item.day).padStart(2, "0")} / 07`;
  mapCard.innerHTML = `
    <div class="card-top"><span class="card-day">DAY ${item.day} · ${item.listTitle.toUpperCase()}</span><span class="card-time">${item.time}</span></div>
    <h3>${item.title}</h3>
    <p>${item.description}</p>
    <div class="card-tags">${item.tags.map(tag => `<span>${tag}</span>`).join("")}</div>
  `;
  mapCard.classList.add("visible");
  if (options.scroll) document.querySelector(`.day-item[data-day="${activeIndex}"]`).scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
}

function stopTour() {
  window.clearInterval(playTimer);
  playTimer = null;
  playButton.classList.remove("is-playing");
  playButton.innerHTML = "<span>▶</span> Play route";
}

function playTour() {
  if (playTimer) return stopTour();
  selectDay(0, { scroll: true });
  playButton.classList.add("is-playing");
  playButton.innerHTML = "<span>■</span> Pause";
  playTimer = window.setInterval(() => {
    if (activeIndex === days.length - 1) return stopTour();
    selectDay(activeIndex + 1, { scroll: true });
  }, 2200);
}

dayList.addEventListener("click", event => {
  const button = event.target.closest(".day-item");
  if (!button) return;
  stopTour();
  selectDay(Number(button.dataset.day));
});

document.querySelectorAll(".port-marker").forEach(marker => marker.addEventListener("click", () => {
  stopTour();
  let index = days.findIndex(day => day.stop === marker.dataset.stop);
  if (marker.dataset.stop === "kahului" && activeIndex === 1) index = 2;
  selectDay(index, { scroll: true });
}));

document.querySelector("#previousDay").addEventListener("click", () => { stopTour(); selectDay(activeIndex - 1, { scroll: true }); });
document.querySelector("#nextDay").addEventListener("click", () => { stopTour(); selectDay(activeIndex + 1, { scroll: true }); });
document.querySelector("#resetMap").addEventListener("click", () => { stopTour(); selectDay(0, { scroll: true }); });
playButton.addEventListener("click", playTour);

const helpDialog = document.querySelector("#helpDialog");
document.querySelector("#helpButton").addEventListener("click", () => helpDialog.showModal());
document.querySelector("#closeHelp").addEventListener("click", () => helpDialog.close());
document.querySelector("#startTour").addEventListener("click", () => { helpDialog.close(); playTour(); });
helpDialog.addEventListener("click", event => {
  if (event.target === helpDialog) helpDialog.close();
});

document.addEventListener("keydown", event => {
  if (event.key === "ArrowRight") { stopTour(); selectDay(activeIndex + 1, { scroll: true }); }
  if (event.key === "ArrowLeft") { stopTour(); selectDay(activeIndex - 1, { scroll: true }); }
});

selectDay(0);
