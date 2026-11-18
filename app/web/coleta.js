let trechoId = null;
let trechoNome = null;
let trechos = [];

function mostrar(id) {
  document.getElementById(id).classList.remove("escondido");
}

function esconder(id) {
  document.getElementById(id).classList.add("escondido");
}

function rodape(passo) {
  const ids = ["btn-gravar", "confirmar", "mudar-endereco", "btn-camera", "btn-mapa"];
  ids.forEach(esconder);
  if (passo === "inicio") {
    mostrar("btn-gravar");
  } else if (passo === "confirmar") {
    mostrar("confirmar");
    mostrar("mudar-endereco");
  } else if (passo === "camera") {
    mostrar("btn-camera");
  } else if (passo === "mapa") {
    mostrar("btn-mapa");
  }
}

function marcarEscolhido(id, nome) {
  trechoId = id;
  trechoNome = nome;
  esconder("inicio");
  esconder("escolha");
  mostrar("captura");
  rodape("camera");
}

function mostrarLista() {
  mostrar("lista-trechos");
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

function semTrechoPerto() {
  esconder("inicio");
  mostrar("escolha");
  esconder("voce-esta");
  document.getElementById("mensagem-gps").textContent =
    "Não achamos um trecho cadastrado perto de você";
  mostrarLista();
  rodape("vazio");
}

function pedirGps() {
  document.getElementById("btn-gravar").disabled = true;
  if (!navigator.geolocation) {
    document.getElementById("btn-gravar").disabled = false;
    semTrechoPerto();
    return;
  }
  navigator.geolocation.getCurrentPosition(
    async (posicao) => {
      document.getElementById("btn-gravar").disabled = false;
      const params = new URLSearchParams({
        lat: String(posicao.coords.latitude),
        lon: String(posicao.coords.longitude),
      });
      const corpo = await fetch("/localizacao?" + params.toString()).then((r) => r.json());
      if (!corpo.trecho) {
        semTrechoPerto();
        return;
      }
      esconder("inicio");
      mostrar("escolha");
      const titulo = document.getElementById("voce-esta");
      titulo.innerHTML = "Você está em <span></span>";
      titulo.querySelector("span").textContent = corpo.trecho.nome;
      titulo.classList.remove("escondido");
      document.getElementById("mensagem-gps").textContent = "";
      esconder("lista-trechos");
      document.getElementById("confirmar").dataset.id = corpo.trecho.id;
      document.getElementById("confirmar").dataset.nome = corpo.trecho.nome;
      rodape("confirmar");
    },
    () => {
      document.getElementById("btn-gravar").disabled = false;
      semTrechoPerto();
    }
  );
}

document.getElementById("btn-gravar").addEventListener("click", pedirGps);

document.getElementById("confirmar").addEventListener("click", (evento) => {
  const botao = evento.currentTarget;
  marcarEscolhido(botao.dataset.id, botao.dataset.nome);
});

document.getElementById("mudar-endereco").addEventListener("click", () => {
  mostrarLista();
  rodape("vazio");
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

function mostrarNota(corpo) {
  const resultado = document.getElementById("resultado");
  resultado.classList.remove("escondido");
  resultado.innerHTML =
    '<p>Nota</p><p class="nota ' +
    corpo.cor +
    '">' +
    corpo.nota +
    "</p>";
  rodape("mapa");
}

function perguntarAndamento(codigo, intervaloMs, pararRelogio) {
  const consultar = async () => {
    const resposta = await fetch("/processamentos/" + codigo);
    const corpo = await resposta.json();
    if (corpo.status === "pronto") {
      clearInterval(laço);
      pararRelogio();
      esconder("processando");
      mostrarNota(corpo);
      return;
    }
    if (corpo.status === "erro") {
      clearInterval(laço);
      pararRelogio();
      esconder("processando");
      const resultado = document.getElementById("resultado");
      resultado.classList.remove("escondido");
      resultado.textContent = "Não foi possível processar. Tente de novo.";
      rodape("inicio");
    }
  };
  const laço = setInterval(consultar, intervaloMs);
}

function enviar(arquivo) {
  esconder("captura");
  rodape("vazio");
  mostrar("envio");
  esconder("processando");
  esconder("resultado");
  document.getElementById("barra").value = 0;

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
      document.getElementById("barra").value = Math.round((evento.loaded / evento.total) * 100);
    }
  };
  xhr.upload.onload = () => {
    esconder("envio");
    mostrar("processando");
    let segundos = 0;
    timerRelogio = setInterval(() => {
      segundos += 1;
      document.getElementById("segundos").textContent = segundos + " s";
    }, 1000);
  };
  xhr.onload = () => {
    if (xhr.status >= 400) {
      pararRelogio();
      esconder("processando");
      const resultado = document.getElementById("resultado");
      resultado.classList.remove("escondido");
      resultado.textContent = "Não foi possível processar. Tente de novo.";
      rodape("inicio");
      return;
    }
    const corpo = JSON.parse(xhr.responseText);
    perguntarAndamento(corpo.codigo, (corpo.intervalo_s || 3) * 1000, pararRelogio);
  };
  xhr.onerror = () => {
    pararRelogio();
    esconder("processando");
    const resultado = document.getElementById("resultado");
    resultado.classList.remove("escondido");
    resultado.textContent = "Falha de rede.";
    rodape("inicio");
  };
  xhr.send(dados);
}

rodape("inicio");
carregarTrechos();
