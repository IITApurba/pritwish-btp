const form = document.getElementById("search-form");
const input = document.getElementById("protein");
const datalist = document.getElementById("suggestions");
const box = document.getElementById("result");

const COLORS = { PB1: "#2a78d6", PB2: "#eb6834", PA: "#1baf7a", NP: "#6250d6", DDX3X: "#52514e" };

function badge(label, kind) {
  const el = document.createElement("span");
  el.className = "badge";
  el.textContent = label;
  el.style.background = COLORS[label] || "#52514e";
  el.title = kind;
  return el;
}

async function check(protein) {
  const res = await fetch("/api/lookup?protein=" + encodeURIComponent(protein));
  const data = await res.json();

  box.hidden = false;
  box.className = data.found ? "found" : "notfound";
  document.getElementById("result-title").textContent = data.found ? data.gene : data.query || "—";
  document.getElementById("result-sub").textContent = data.found
    ? [data.protein_name, data.uniprot.join(", ")].filter(Boolean).join(" · ")
    : "";

  const badges = document.getElementById("badges");
  badges.replaceChildren();
  data.rnps.forEach((r) => badges.append(badge(r, "RNP")));
  data.interactome.forEach((i) => badges.append(badge(i, "Human interactome")));

  document.getElementById("result-text").textContent = data.message;
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  check(input.value);
});

input.addEventListener("input", async () => {
  if (input.value.trim().length < 2) return;
  const res = await fetch("/api/suggest?q=" + encodeURIComponent(input.value));
  const items = await res.json();
  datalist.replaceChildren(...items.map((g) => Object.assign(document.createElement("option"), { value: g })));
});

document.querySelectorAll(".example").forEach((a) =>
  a.addEventListener("click", (e) => {
    e.preventDefault();
    input.value = a.textContent;
    check(a.textContent);
  })
);
