const cardsArea = document.getElementById("cards-area");
const cardTemplate = document.getElementById("card-template");
const subnetSelect = document.getElementById("subnet-select");
const scanButton = document.getElementById("scan-button");
const scanStatus = document.getElementById("scan-status");
const onlineCount = document.getElementById("online-count");
const offlineCount = document.getElementById("offline-count");

const cardElements = new Map();
const studentInputsFocused = new Set();

function initials(name) {
  const parts = (name || "").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "--";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

const AVATAR_COLORS = ["#3b82f6", "#a855f7", "#ec4899", "#f59e0b", "#22c55e", "#06b6d4"];
function avatarColor(name) {
  if (!name) return "#4b5563";
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}

function formatElapsed(seconds) {
  if (seconds < 60) return `há ${Math.floor(seconds)}s`;
  return `há ${Math.floor(seconds / 60)} min`;
}

function formatTick(value) {
  const abs = Math.abs(value);
  const decimals = abs !== 0 && abs < 10 ? 1 : 0;
  return value.toFixed(decimals);
}

function drawChart(canvas, series) {
  const axisWidth = 36;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight || 90;
  if (canvas.width !== width) canvas.width = width;
  if (canvas.height !== height) canvas.height = height;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, width, height);

  const plotX0 = axisWidth;
  const plotWidth = Math.max(1, width - axisWidth);
  const padding = 6;
  const usableH = height - 2 * padding;

  const allValues = series.flatMap((s) => s.values || []);
  const vmin = allValues.length ? Math.min(...allValues) : 0;
  const vmax = allValues.length ? Math.max(...allValues) : 1;
  const span = vmax - vmin || 1;

  ctx.strokeStyle = "#232a35";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#5b6472";
  ctx.font = "10px system-ui, sans-serif";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  const ticks = 4;
  for (let i = 0; i <= ticks; i++) {
    const y = padding + (usableH * i) / ticks;
    ctx.beginPath();
    ctx.moveTo(plotX0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
    const value = vmax - (span * i) / ticks;
    ctx.fillText(formatTick(value), plotX0 - 6, y);
  }

  if (allValues.length < 2) return;

  for (const { values, color } of series) {
    if (!values || values.length < 2) continue;
    const stepX = plotWidth / (values.length - 1);
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    values.forEach((value, idx) => {
      const x = plotX0 + idx * stepX;
      const norm = (value - vmin) / span;
      const y = padding + (1 - norm) * usableH;
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
}

function buildCard(plcId) {
  const node = cardTemplate.content.firstElementChild.cloneNode(true);
  node.dataset.id = plcId;

  const studentInput = node.querySelector(".student-input");
  studentInput.addEventListener("focus", () => studentInputsFocused.add(plcId));
  studentInput.addEventListener("blur", () => {
    studentInputsFocused.delete(plcId);
    window.pywebview.api.set_student(plcId, studentInput.value);
  });
  studentInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") studentInput.blur();
  });

  node.querySelector(".remove-btn").addEventListener("click", () => {
    if (!confirm("Remover este CLP da lista e parar o monitoramento?")) return;
    window.pywebview.api.remove_plc(plcId);
  });

  cardsArea.appendChild(node);
  cardElements.set(plcId, node);
  return node;
}

function updateCard(node, card) {
  node.querySelector(".plc-name").textContent = card.name;
  node.querySelector(".plc-ip").textContent = `${card.ip} · OPC-UA`;

  const pill = node.querySelector(".status-pill");
  pill.classList.toggle("online", card.online);
  pill.classList.toggle("offline", !card.online);
  pill.querySelector(".status-text").textContent = card.online ? "CONECTADO" : "DESCONECTADO";

  const avatar = node.querySelector(".avatar");
  avatar.textContent = initials(card.student);
  avatar.style.background = avatarColor(card.student);

  const studentInput = node.querySelector(".student-input");
  if (!studentInputsFocused.has(card.id) && studentInput.value !== card.student) {
    studentInput.value = card.student || "";
  }

  const offlineMsg = node.querySelector(".offline-msg");
  if (card.online) {
    offlineMsg.textContent = "";
  } else if (card.last_data_at) {
    const elapsed = Date.now() / 1000 - card.last_data_at;
    offlineMsg.textContent = `Último dado recebido ${formatElapsed(elapsed)} — aguardando reconexão`;
  } else {
    offlineMsg.textContent = "Aguardando conexão...";
  }

  const style = getComputedStyle(document.documentElement);
  drawChart(node.querySelector(".chart-y"), [
    { values: card.y, color: style.getPropertyValue("--chart-green") },
    { values: card.setpoint, color: style.getPropertyValue("--chart-amber") },
  ]);
  drawChart(node.querySelector(".chart-u"), [{ values: card.u, color: style.getPropertyValue("--chart-blue") }]);

  node.querySelector(".tile-overshoot").textContent = card.overshoot_pct != null ? `${card.overshoot_pct}%` : "—";
  node.querySelector(".tile-peak").textContent = card.peak_time_s != null ? `${card.peak_time_s}s` : "—";
  node.querySelector(".tile-settle").textContent = card.settling_time_s != null ? `${card.settling_time_s}s` : "—";
  node.querySelector(".tile-error").textContent =
    card.steady_state_error_pct != null ? `${card.steady_state_error_pct}%` : "—";
  node.querySelector(".tile-iae").textContent = card.iae != null ? card.iae.toFixed(2) : "—";
}

async function refreshState() {
  try {
    const state = await window.pywebview.api.get_state();
    onlineCount.textContent = state.online;
    offlineCount.textContent = state.offline;

    const seenIds = new Set();
    for (const card of state.cards) {
      seenIds.add(card.id);
      const node = cardElements.get(card.id) || buildCard(card.id);
      updateCard(node, card);
    }
    for (const [id, node] of cardElements.entries()) {
      if (!seenIds.has(id)) {
        node.remove();
        cardElements.delete(id);
      }
    }
  } catch (err) {
    console.error("refreshState failed", err);
  }
}

async function loadSubnets() {
  try {
    const subnets = await window.pywebview.api.get_subnets();
    subnetSelect.innerHTML = "";
    for (const subnet of subnets) {
      const option = document.createElement("option");
      option.value = subnet;
      option.textContent = subnet;
      subnetSelect.appendChild(option);
    }
  } catch (err) {
    console.error("loadSubnets failed", err);
  }
}

async function runScan() {
  const subnet = subnetSelect.value;
  if (!subnet) return;
  scanButton.disabled = true;
  scanStatus.textContent = "Buscando...";
  try {
    const result = await window.pywebview.api.scan(subnet);
    scanStatus.textContent = `${result.found} encontrado(s)`;
    await refreshState();
  } catch (err) {
    scanStatus.textContent = "Erro na varredura.";
    console.error(err);
  } finally {
    scanButton.disabled = false;
  }
}

window.addEventListener("pywebviewready", () => {
  loadSubnets();
  refreshState();
  setInterval(refreshState, 500);
  scanButton.addEventListener("click", runScan);
});
