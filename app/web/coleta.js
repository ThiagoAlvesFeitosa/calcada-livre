const GPS_OPCOES = { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 };

let inicio = null;
let nomeRua = "Local sem nome";
let videoArquivo = null;
let candidato = null;

function mostrar(id) {
  document.getElementById(id).classList.remove("escondido");
}

function esconder(id) {
  document.getElementById(id).classList.add("escondido");
}

function rodape(passo) {
  ["btn-gravar", "confirmar", "corrigir", "btn-sim", "btn-nao", "btn-mapa"].forEach(esconder);
  if (passo === "inicio") {
    mostrar("btn-gravar");
  } else if (passo === "confirmar") {
    mostrar("confirmar");
    mostrar("corrigir");
  } else if (passo === "mesma") {
    mostrar("btn-sim");
    mostrar("btn-nao");
  } else if (passo === "mapa") {
    mostrar("btn-mapa");
  }
}

function obterGps() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("sem-gps"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (posicao) => {
        resolve({
          lat: posicao.coords.latitude,
          lon: posicao.coords.longitude,
        });
      },
      () => reject(new Error("falha")),
      GPS_OPCOES
    );
  });
}

function mostrarRua(nome) {
  esconder("inicio");
  mostrar("escolha");
  const titulo = document.getElementById("voce-esta");
  titulo.innerHTML = "Você está na <span></span>";
  titulo.querySelector("span").textContent = nome;
  titulo.classList.remove("escondido");
  document.getElementById("mensagem-gps").textContent = "";
  rodape("confirmar");
}

async function pedirInicio() {
  const botao = document.getElementById("btn-gravar");
  botao.disabled = true;
  esconder("inicio");
  mostrar("escolha");
  esconder("voce-esta");
  document.getElementById("mensagem-gps").textContent = "Buscando sua localização…";
  try {
    inicio = await obterGps();
    const resposta = await fetch(
      "/endereco?" + new URLSearchParams({ lat: String(inicio.lat), lon: String(inicio.lon) })
    );
    const corpo = await resposta.json();
    if (corpo.gps_espera_s) {
      GPS_OPCOES.timeout = Number(corpo.gps_espera_s) * 1000;
    }
    nomeRua = corpo.nome || "Local sem nome";
    mostrarRua(nomeRua);
  } catch (erro) {
    esconder("inicio");
    mostrar("escolha");
    esconder("voce-esta");
    document.getElementById("mensagem-gps").textContent =
      "Abra pelo link seguro para usar a localização";
    rodape("inicio");
  } finally {
    botao.disabled = false;
  }
}

document.getElementById("btn-gravar").addEventListener("click", pedirInicio);

document.getElementById("corrigir").addEventListener("click", () => {
  const novo = window.prompt("Nome da rua", nomeRua);
  if (novo && novo.trim()) {
    nomeRua = novo.trim();
    mostrarRua(nomeRua);
  }
});

document.getElementById("confirmar").addEventListener("click", () => {
  document.getElementById("video").click();
});

document.getElementById("video").addEventListener("change", async (evento) => {
  const arquivo = evento.target.files[0];
  evento.target.value = "";
  if (!arquivo || !inicio) {
    return;
  }
  videoArquivo = arquivo;
  esconder("voce-esta");
  mostrar("escolha");
  document.getElementById("mensagem-gps").textContent = "Lendo o ponto de fim…";
  rodape("vazio");
  let fim = null;
  try {
    fim = await obterGps();
  } catch (erro) {
    fim = null;
  }
  esconder("escolha");
  const params = new URLSearchParams({
    lat_inicio: String(inicio.lat),
    lon_inicio: String(inicio.lon),
    rua: nomeRua,
  });
  if (fim) {
    params.set("lat_fim", String(fim.lat));
    params.set("lon_fim", String(fim.lon));
  }
  const corpo = await fetch("/trechos/candidatos?" + params.toString()).then((r) => r.json());
  candidato = corpo.candidato || null;
  window._fimGps = fim;
  if (candidato) {
    mostrar("mesma");
    const data = candidato.data ? " filmada em " + candidato.data : "";
    document.getElementById("pergunta-mesma").textContent =
      "Parece a mesma calçada" + data + ". É a mesma?";
    rodape("mesma");
    return;
  }
  enviarRelato("nao", "");
});

document.getElementById("btn-sim").addEventListener("click", () => {
  enviarRelato("sim", candidato ? candidato.id : "");
});

document.getElementById("btn-nao").addEventListener("click", () => {
  enviarRelato("nao", "");
});

function mostrarNota(corpo) {
  const resultado = document.getElementById("resultado");
  resultado.classList.remove("escondido");
  resultado.innerHTML =
    '<p>Nota</p><p class="nota ' + corpo.cor + '">' + corpo.nota + "</p>";
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

function enviarRelato(atualizar, mesmoId) {
  esconder("mesma");
  mostrar("envio");
  rodape("vazio");
  document.getElementById("barra").value = 0;
  const fim = window._fimGps;
  const dados = new FormData();
  dados.append("video", videoArquivo);
  dados.append("lat_inicio", String(inicio.lat));
  dados.append("lon_inicio", String(inicio.lon));
  dados.append("nome", nomeRua);
  dados.append("atualizar", atualizar);
  dados.append("mesmo_trecho_id", mesmoId);
  if (fim) {
    dados.append("lat_fim", String(fim.lat));
    dados.append("lon_fim", String(fim.lon));
  }

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
