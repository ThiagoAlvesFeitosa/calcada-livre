const passos = [
  "1. Celular deitado, na altura do peito, apontado para a calçada 3 a 5 m à frente.",
  "2. Ande devagar e sem parar.",
  "3. Um vídeo por face de quadra, até 60 segundos.",
];

const cores = { verde: "#2e7d32", amarelo: "#f9a825", vermelho: "#c62828", cinza: "#9e9e9e" };

let passoAtual = 0;
let trechoId = null;
let mapa = null;

function corLinha(propriedades) {
  if (!propriedades.filmado || !propriedades.cor) {
    return cores.cinza;
  }
  return cores[propriedades.cor] || cores.cinza;
}

async function carregarMapa() {
  mapa = L.map("mapa").setView([-22.2175, -49.9463], 18);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
  }).addTo(mapa);
  const geojson = await fetch("/trechos").then((r) => r.json());
  const camada = L.geoJSON(geojson, {
    style: (feature) => ({
      color: corLinha(feature.properties),
      weight: 7,
    }),
    onEachFeature: (feature, layer) => {
      layer.on("click", () => {
        trechoId = feature.properties.id || feature.id;
        document.getElementById("trecho-escolhido").textContent =
          "Trecho: " + (feature.properties.nome || trechoId);
      });
    },
  }).addTo(mapa);
  if (camada.getBounds().isValid()) {
    mapa.fitBounds(camada.getBounds(), { padding: [20, 20] });
  }
}

document.getElementById("proximo-passo").addEventListener("click", () => {
  passoAtual += 1;
  if (passoAtual >= passos.length) {
    document.getElementById("tutorial").classList.add("escondido");
    return;
  }
  document.getElementById("passo-texto").textContent = passos[passoAtual];
  if (passoAtual === passos.length - 1) {
    document.getElementById("proximo-passo").textContent = "Entendi";
  }
});

document.getElementById("video").addEventListener("change", (evento) => {
  const arquivo = evento.target.files[0];
  if (!arquivo) {
    return;
  }
  if (!trechoId) {
    alert("Escolha o trecho no mapa antes de enviar.");
    evento.target.value = "";
    return;
  }
  enviar(arquivo);
});

function enviar(arquivo) {
  const envio = document.getElementById("envio");
  const processando = document.getElementById("processando");
  const resultado = document.getElementById("resultado");
  const barra = document.getElementById("barra");
  envio.classList.remove("escondido");
  processando.classList.add("escondido");
  resultado.classList.add("escondido");
  barra.value = 0;

  const dados = new FormData();
  dados.append("trecho_id", trechoId);
  dados.append("video", arquivo);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/videos");
  xhr.upload.onprogress = (evento) => {
    if (evento.lengthComputable) {
      barra.value = Math.round((evento.loaded / evento.total) * 100);
    }
  };
  xhr.upload.onload = () => {
    envio.classList.add("escondido");
    processando.classList.remove("escondido");
    let segundos = 0;
    const rotulo = document.getElementById("segundos");
    const timer = setInterval(() => {
      segundos += 1;
      rotulo.textContent = segundos + " s";
    }, 1000);
    xhr.addEventListener("loadend", () => clearInterval(timer), { once: true });
  };
  xhr.onload = () => {
    processando.classList.add("escondido");
    if (xhr.status >= 400) {
      resultado.classList.remove("escondido");
      resultado.textContent = "Não foi possível processar. Tente de novo.";
      return;
    }
    const corpo = JSON.parse(xhr.responseText);
    resultado.classList.remove("escondido");
    resultado.innerHTML =
      '<p>Nota</p><p class="nota ' +
      corpo.cor +
      '">' +
      corpo.nota +
      "</p><p>Cor: " +
      corpo.cor +
      "</p><p>Obstáculos por 100 m: " +
      Number(corpo.obstaculos_por_100m).toFixed(1) +
      "</p>";
    carregarMapa();
  };
  xhr.onerror = () => {
    processando.classList.add("escondido");
    resultado.classList.remove("escondido");
    resultado.textContent = "Falha de rede.";
  };
  xhr.send(dados);
}

carregarMapa();
