const cores = { verde: "#2e7d32", amarelo: "#f9a825", vermelho: "#c62828", cinza: "#9e9e9e" };

function corLinha(propriedades) {
  if (!propriedades.filmado || !propriedades.cor) {
    return cores.cinza;
  }
  return cores[propriedades.cor] || cores.cinza;
}

function listaTipos(porTipo) {
  const entradas = Object.entries(porTipo || {});
  if (!entradas.length) {
    return "<p>Nenhum obstáculo no caminho.</p>";
  }
  return (
    "<ul>" +
    entradas
      .map(([classe, quantidade]) => "<li>" + classe + ": " + quantidade + "</li>")
      .join("") +
    "</ul>"
  );
}

async function mostrarDetalhe(trechoId) {
  const detalhe = await fetch("/trechos/" + encodeURIComponent(trechoId)).then((r) => r.json());
  const caixa = document.getElementById("detalhe");
  caixa.classList.remove("escondido");
  if (detalhe.nota === null) {
    caixa.innerHTML = "<p><strong>" + detalhe.nome + "</strong></p><p>Ainda não filmado.</p>";
    return;
  }
  const fotos = (detalhe.quadros || [])
    .map((url) => '<img src="' + url + '" alt="Quadro anotado">')
    .join("");
  caixa.innerHTML =
    "<p><strong>" +
    detalhe.nome +
    '</strong></p><p class="nota ' +
    detalhe.cor +
    '">' +
    detalhe.nota +
    "</p><p>Cor: " +
    detalhe.cor +
    "</p><p>Data: " +
    (detalhe.data || "—") +
    "</p>" +
    listaTipos(detalhe.obstaculos_por_tipo) +
    '<div class="quadros">' +
    fotos +
    "</div>";
}

async function iniciar() {
  const mapa = L.map("mapa").setView([-22.2175, -49.9463], 18);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
  }).addTo(mapa);

  const [geojson, censo] = await Promise.all([
    fetch("/trechos").then((r) => r.json()),
    fetch("/censo").then((r) => r.json()),
  ]);

  document.getElementById("censo").innerHTML =
    "<p>Trechos filmados sem obstáculo no caminho: <strong>" +
    censo.sem_obstaculo +
    " de " +
    censo.filmados +
    "</strong></p><p>Censo 2022, Marília: <strong>46,4%</strong> dos moradores em calçada desobstruída</p>" +
    '<p class="legenda">referência; não é a mesma medida</p>';

  const camada = L.geoJSON(geojson, {
    style: (feature) => ({ color: corLinha(feature.properties), weight: 7 }),
    onEachFeature: (feature, layer) => {
      layer.on("click", () => {
        const id = feature.properties.id || feature.id;
        mostrarDetalhe(id);
      });
    },
  }).addTo(mapa);
  if (camada.getBounds().isValid()) {
    mapa.fitBounds(camada.getBounds(), { padding: [20, 20] });
  }
}

iniciar();
