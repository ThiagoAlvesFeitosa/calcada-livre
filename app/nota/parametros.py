NOTA_INICIAL = 100
NOTA_MINIMA = 0
METROS_REFERENCIA = 100

DESCONTO_BLOQUEIO = 15
DESCONTO_PARCIAL = 8
DESCONTO_BARREIRA = 10

LIMITE_OCUPACAO_BLOQUEIO = 0.5

LIMITE_VERDE = 80
LIMITE_AMARELO = 50

CLASSES_BARREIRA = frozenset({"pothole", "stairs", "buraco", "degrau"})

RAIO_TERRA_M = 6_371_000
BYTES_POR_MEGABYTE = 1024 * 1024
EXTENSOES_VIDEO = frozenset({".mp4", ".webm", ".mov", ".m4v"})

CENSO_CALCADA_DESOBSTRUIDA = 0.464

COR_VERDE = "#2e7d32"
COR_AMARELO = "#f9a825"
COR_VERMELHO = "#c62828"
COR_CINZA = "#9e9e9e"

QUADROS_NO_DETALHE = 3
ESPESSURA_LINHA_MAPA = 8
DISTANCIA_MAXIMA_TRECHO_M = 50
DISTANCIA_MESMO_TRECHO_M = 15
COMPRIMENTO_PONTO_M = 10
GPS_ESPERA_S = 10
GEOCODIFICADOR_TIMEOUT_S = 5
NOME_LOCAL_SEM_NOME = "Local sem nome"
GEOCODIFICADOR_USER_AGENT = "CalcadaLivre-FIAP/1.0 (https://github.com/ThiagoAlvesFeitosa/calcada-livre)"
ARQUIVO_COLECAO_TRECHOS = "trechos.geojson"
FUSO_BRASILIA = "America/Sao_Paulo"

NOMES_CLASSES_PT: dict[str, str] = {
    "pole": "poste",
    "tree": "árvore",
    "trash bin": "lixeira",
    "car": "carro",
    "motorcycle": "moto",
    "pothole": "buraco",
    "stairs": "degrau",
    "construction debris": "entulho",
    "sand pile": "areia",
    "bricks": "tijolos",
    "cardboard box": "caixa de papelão",
    "bench": "banco",
    "sign": "placa",
    "person": "pessoa",
    "license plate": "placa",
}
