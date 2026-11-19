function corCss(nome) {
  return getComputedStyle(document.documentElement).getPropertyValue(nome).trim();
}

function corLinha(cor) {
  const chave = {
    verde: "--nota-verde",
    amarelo: "--nota-amarelo",
    vermelho: "--nota-vermelho",
  }[cor];
  return chave ? corCss(chave) : corCss("--cinza");
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

function abrirFicha(html) {
  const ficha = document.getElementById("ficha");
  ficha.hidden = false;
  ficha.classList.remove("escondido");
  ficha.innerHTML = html;
}

async function mostrarDetalhe(trechoId) {
  const detalhe = await fetch("/trechos/" + encodeURIComponent(trechoId)).then((r) => r.json());
  if (detalhe.nota === null) {
    return;
  }
  const fotos = (detalhe.quadros || [])
    .map((url) => '<img src="' + url + '" alt="Quadro anotado da calçada">')
    .join("");
  abrirFicha(
    "<h2>" +
      detalhe.nome +
      '</h2><p class="nota ' +
      detalhe.cor +
      '">' +
      detalhe.nota +
      "</p>" +
      listaTipos(detalhe.obstaculos_por_tipo) +
      "<p>Data: " +
      (detalhe.data || "—") +
      "</p>" +
      '<div class="quadros">' +
      fotos +
      "</div>"
  );
}

async function iniciar() {
  const mapa = L.map("mapa", { zoomControl: true }).setView([-22.2175, -49.9463], 18);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
  }).addTo(mapa);

  const geojson = await fetch("/trechos").then((r) => r.json());
  const filmados = {
    type: "FeatureCollection",
    features: (geojson.features || []).filter((feature) => feature.properties && feature.properties.filmado),
  };

  const espessura = Number(corCss("--espessura-linha")) || 8;
  const vermelho = corCss("--nota-vermelho");
  const camada = L.geoJSON(filmados, {
    style: (feature) => ({
      color: corLinha(feature.properties.cor),
      weight: espessura,
      opacity: 1,
    }),
    pointToLayer: (feature, latlng) =>
      L.circle(latlng, {
        radius: Number(feature.properties.raio_m),
        color: corLinha(feature.properties.cor),
        fillColor: corLinha(feature.properties.cor),
        fillOpacity: 0.35,
        weight: 2,
      }),
    onEachFeature: (feature, layer) => {
      layer.on("click", () => {
        mostrarDetalhe(feature.properties.id || feature.id);
      });
    },
  }).addTo(mapa);

  filmados.features.forEach((feature) => {
    (feature.properties.pontos_obstaculos || []).forEach((ponto) => {
      L.circleMarker([ponto.lat, ponto.lon], {
        radius: 7,
        color: vermelho,
        fillColor: vermelho,
        fillOpacity: 1,
        weight: 1,
      })
        .addTo(mapa)
        .on("click", () => mostrarDetalhe(feature.properties.id || feature.id));
    });
  });

  if (camada.getBounds().isValid()) {
    mapa.fitBounds(camada.getBounds(), { padding: [40, 40], maxZoom: 19 });
  }
}

iniciar();
