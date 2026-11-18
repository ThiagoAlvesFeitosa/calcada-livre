const passos = [
  "1. Celular deitado, na altura do peito, apontado para a calçada 3 a 5 m à frente.",
  "2. Ande devagar e sem parar.",
  "3. Um vídeo por face de quadra, até 30 segundos.",
];

let passoAtual = 0;
let trechoId = null;
let trechoNome = null;
let trechos = [];

function marcarEscolhido(id, nome) {
  trechoId = id;
  trechoNome = nome;
  document.getElementById("trecho-escolhido").textContent = "Trecho: " + nome;
}

function mostrarLista() {
  document.getElementById("rotulo-lista").classList.remove("escondido");
  document.getElementById("lista-trechos").classList.remove("escondido");
}

function esconderConfirmacao() {
  document.getElementById("confirmacao").classList.add("escondido");
  document.getElementById("confirmar").classList.add("escondido");
  document.getElementById("escolher-outro").classList.add("escondido");
}

function montarLista() {
  const lista = document.getElementById("lista-trechos");
  lista.innerHTML = "";
  trechos.forEach((item) => {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "secundario";
    botao.textContent = item.nome;
    botao.addEventListener("click", () => {
      marcarEscolhido(item.id, item.nome);
      esconderConfirmacao();
    });
    const li = document.createElement("li");
    li.appendChild(botao);
    lista.appendChild(li);
  });
}

async function carregarTrechos() {
  const geojson = await fetch("/trechos").then((r) => r.json());
  trechos = (geojson.features || []).map((feature) => ({
    id: feature.properties.id || feature.id,
    nome: feature.properties.nome || feature.id,
  }));
  montarLista();
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

document.getElementById("usar-localizacao").addEventListener("click", () => {
  if (!navigator.geolocation) {
    mostrarLista();
    document.getElementById("trecho-escolhido").textContent =
      "Sem GPS neste navegador. Escolha o trecho na lista.";
    return;
  }
  navigator.geolocation.getCurrentPosition(
    async (posicao) => {
      const params = new URLSearchParams({
        lat: String(posicao.coords.latitude),
        lon: String(posicao.coords.longitude),
      });
      const corpo = await fetch("/localizacao?" + params.toString()).then((r) => r.json());
      if (!corpo.trecho) {
        mostrarLista();
        document.getElementById("trecho-escolhido").textContent =
          "Você não está perto de um trecho do mapa. Escolha na lista.";
        return;
      }
      document.getElementById("confirmacao").textContent =
        "Você está em " + corpo.trecho.nome + " — confirmar?";
      document.getElementById("confirmacao").classList.remove("escondido");
      document.getElementById("confirmar").classList.remove("escondido");
      document.getElementById("escolher-outro").classList.remove("escondido");
      document.getElementById("confirmar").dataset.id = corpo.trecho.id;
      document.getElementById("confirmar").dataset.nome = corpo.trecho.nome;
    },
    () => {
      mostrarLista();
      document.getElementById("trecho-escolhido").textContent =
        "Não deu para usar a localização. Escolha o trecho na lista.";
    }
  );
});

document.getElementById("confirmar").addEventListener("click", (evento) => {
  const botao = evento.currentTarget;
  marcarEscolhido(botao.dataset.id, botao.dataset.nome);
  esconderConfirmacao();
});

document.getElementById("escolher-outro").addEventListener("click", () => {
  esconderConfirmacao();
  mostrarLista();
});

document.getElementById("video").addEventListener("change", (evento) => {
  const arquivo = evento.target.files[0];
  if (!arquivo) {
    return;
  }
  if (!trechoId) {
    alert("Escolha o trecho antes de enviar.");
    evento.target.value = "";
    return;
  }
  enviar(arquivo);
});

function mostrarNota(corpo, processando, resultado) {
  processando.classList.add("escondido");
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
}

function perguntarAndamento(codigo, intervaloMs, processando, resultado, pararRelogio) {
  const consultar = async () => {
    const resposta = await fetch("/processamentos/" + codigo);
    const corpo = await resposta.json();
    if (corpo.status === "pronto") {
      clearInterval(laço);
      pararRelogio();
      mostrarNota(corpo, processando, resultado);
      return;
    }
    if (corpo.status === "erro") {
      clearInterval(laço);
      pararRelogio();
      processando.classList.add("escondido");
      resultado.classList.remove("escondido");
      resultado.textContent = "Não foi possível processar. Tente de novo.";
    }
  };
  const laço = setInterval(consultar, intervaloMs);
}

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

  let timerRelogio = null;
  const pararRelogio = () => {
    if (timerRelogio) {
      clearInterval(timerRelogio);
      timerRelogio = null;
    }
  };

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
    timerRelogio = setInterval(() => {
      segundos += 1;
      rotulo.textContent = segundos + " s";
    }, 1000);
  };
  xhr.onload = () => {
    if (xhr.status >= 400) {
      pararRelogio();
      processando.classList.add("escondido");
      resultado.classList.remove("escondido");
      resultado.textContent = "Não foi possível processar. Tente de novo.";
      return;
    }
    const corpo = JSON.parse(xhr.responseText);
    const intervaloMs = (corpo.intervalo_s || 3) * 1000;
    perguntarAndamento(corpo.codigo, intervaloMs, processando, resultado, pararRelogio);
  };
  xhr.onerror = () => {
    pararRelogio();
    processando.classList.add("escondido");
    resultado.classList.remove("escondido");
    resultado.textContent = "Falha de rede.";
  };
  xhr.send(dados);
}

carregarTrechos();
