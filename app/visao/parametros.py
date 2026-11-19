QUADROS_POR_SEGUNDO = 2

LADO_REFERENCIA_PIXELS = 576
PIXELS_DILATACAO_REFERENCIA = 24
PIXELS_DILATACAO_CALCADA = PIXELS_DILATACAO_REFERENCIA
FRACAO_DILATACAO_CALCADA = PIXELS_DILATACAO_REFERENCIA / LADO_REFERENCIA_PIXELS

CONFIANCA_MINIMA_OBSTACULO = 0.12
CONFIANCA_MINIMA_PRIVACIDADE = 0.08
CONFIANCA_MINIMA_BRUTA = 0.05
CONFIANCA_MINIMA_POR_CLASSE: dict[str, float] = {
    "damaged sidewalk": 0.40,
    "objects on sidewalk": 0.32,
    "construction debris": 0.08,
}
CONFIANCAS_VARREDURA = (0.10, 0.12, 0.15, 0.18, 0.20, 0.25)
FRACOES_CAMINHO_VARREDURA = (0.45, 0.55, 0.65)
CLASSES_CORTE_MENOR = ("construction debris", "sand pile", "bricks")

FRACAO_INFERIOR_VEICULO = 1.0
FRACAO_EXTENSAO_INFERIOR_VEICULO = 0.8
FRACAO_CAMINHO_INFERIOR_PAISAGEM = 0.65
FRACAO_CAMINHO_INFERIOR_RETRATO = 0.65
FRACAO_CAMINHO_INFERIOR = FRACAO_CAMINHO_INFERIOR_PAISAGEM
FRACAO_LARGURA_CORREDOR_CENTRAL_PAISAGEM = 0.5
FRACAO_LARGURA_CORREDOR_CENTRAL_RETRATO = 0.5
FRACAO_LARGURA_CORREDOR_CENTRAL = FRACAO_LARGURA_CORREDOR_CENTRAL_PAISAGEM
FRACAO_MINIMA_CHAO_LIVRE = 0.28
SEGUNDOS_MINIMOS_OBSTRUCAO = 2.0
SOBREPOSICAO_MAXIMA = 0.5

CLASSE_OBJETO_NO_CAMINHO = "objects on sidewalk"
CLASSE_CALCADA_DANIFICADA = "damaged sidewalk"
CLASSE_CAMINHO_OBSTRUIDO = "blocked path"
CLASSES_NOVAS_SOBREPOSICAO = frozenset({CLASSE_OBJETO_NO_CAMINHO, CLASSE_CALCADA_DANIFICADA})
CLASSES_PROTEGIDAS_SOBREPOSICAO = frozenset({"tree", "trash bin"})
CLASSES_YOLO_PAUSADAS = frozenset({CLASSE_OBJETO_NO_CAMINHO, CLASSE_CALCADA_DANIFICADA})

SEGUNDOS_PARA_JUNTAR_MESMA_CLASSE = 1.5
SEGUNDOS_TOLERANCIA_GABARITO = 2.0

DIVISOES_MOSAICO = 8
PIXELS_MINIMOS_MOSAICO = 8
ESPESSURA_CAIXA = 3
ESCALA_TEXTO_CAIXA = 0.7
ESPESSURA_TEXTO_CAIXA = 2
PROPORCAO_RECORTE_RETRATO = (9, 16)

ID_CLASSE_CALCADA = 1
NOMES_MASCARA_CALCADA = ("sidewalk", "road")

MODELO_SEGFORMER = "nvidia/segformer-b0-finetuned-cityscapes-1024-1024"
ARQUIVO_YOLO_WORLD = "yolov8s-worldv2.pt"

CLASSES_PRIVACIDADE = frozenset({"person", "license plate"})
CLASSES_VEICULO = frozenset({"car", "motorcycle"})
CLASSES_IGNORADAS = frozenset({"bench", "sign"})
CLASSES_FORA_DA_CONTAGEM = CLASSES_PRIVACIDADE | CLASSES_VEICULO | CLASSES_IGNORADAS

MAPA_CLASSES: dict[str, list[str]] = {
    "pole": ["pole", "concrete pillar", "Y-shaped pole"],
    "tree": ["tree"],
    "trash bin": ["trash bin", "garbage bin"],
    "car": ["car"],
    "motorcycle": ["motorcycle"],
    "pothole": ["pothole"],
    "stairs": ["stairs"],
    "construction debris": [
        "construction debris",
        "rubble",
        "debris",
        "rubble pile",
        "pile of rocks",
        "heap of stones",
        "broken concrete",
        "pile of wood",
        "lumber",
        "wooden planks",
        "wood scraps",
        "pile of branches",
        "cut branches on the ground",
    ],
    "objects on sidewalk": [
        "objects on sidewalk",
        "wheelbarrow",
        "construction materials",
        "cement bags",
        "metal bars",
        "rebar",
        "pallet",
        "furniture",
        "mattress",
        "tires",
        "traffic cone",
        "barrier",
        "scooter",
        "bicycle",
    ],
    "damaged sidewalk": [
        "damaged sidewalk",
        "broken sidewalk",
        "damaged pavement",
        "cracked pavement",
        "broken concrete slab",
        "uneven pavement",
        "broken tiles",
        "sidewalk crack",
        "hole in sidewalk",
        "missing paving stones",
        "loose stones",
        "sunken pavement",
        "broken curb",
        "exposed dirt",
        "tree roots on the ground",
        "roots breaking the pavement",
    ],
    "sand pile": ["sand pile", "pile of sand", "gravel pile", "dirt pile"],
    "bricks": ["bricks"],
    "cardboard box": ["cardboard box", "cardboard boxes"],
    "bench": ["bench"],
    "sign": ["sign"],
    "person": ["person"],
    "license plate": ["license plate"],
}


def eh_retrato(altura: int, largura: int) -> bool:
    return int(altura) > int(largura)


def fracao_caminho_inferior(altura: int | None = None, largura: int | None = None) -> float:
    if altura is None or largura is None:
        return FRACAO_CAMINHO_INFERIOR_PAISAGEM
    if eh_retrato(altura, largura):
        return FRACAO_CAMINHO_INFERIOR_RETRATO
    return FRACAO_CAMINHO_INFERIOR_PAISAGEM


def fracao_corredor_central(altura: int | None = None, largura: int | None = None) -> float:
    if altura is None or largura is None:
        return FRACAO_LARGURA_CORREDOR_CENTRAL_PAISAGEM
    if eh_retrato(altura, largura):
        return FRACAO_LARGURA_CORREDOR_CENTRAL_RETRATO
    return FRACAO_LARGURA_CORREDOR_CENTRAL_PAISAGEM


def pixels_proporcionais(referencia: int, altura: int, largura: int) -> int:
    _ = largura
    return max(1, int(round(referencia * max(int(altura), 1) / LADO_REFERENCIA_PIXELS)))


def pixels_dilatacao(altura: int, largura: int) -> int:
    return pixels_proporcionais(PIXELS_DILATACAO_REFERENCIA, altura, largura)


def pixels_mosaico_minimo(altura: int, largura: int) -> int:
    return max(PIXELS_MINIMOS_MOSAICO, pixels_proporcionais(PIXELS_MINIMOS_MOSAICO, altura, largura))


def pixels_espessura_caixa(altura: int, largura: int) -> int:
    return pixels_proporcionais(ESPESSURA_CAIXA, altura, largura)


def nomes_para_yolo() -> list[str]:
    nomes: list[str] = []
    for canonico, variantes in MAPA_CLASSES.items():
        if canonico in CLASSES_IGNORADAS or canonico in CLASSES_YOLO_PAUSADAS:
            continue
        nomes.extend(variantes)
    return nomes


def nome_em_portugues(nome: str) -> str:
    from app.nota.parametros import NOMES_CLASSES_PT

    canonico = classe_nossa(nome)
    return NOMES_CLASSES_PT.get(canonico, canonico)


def etiqueta_quadro(nome: str) -> str:
    texto = nome_em_portugues(nome)
    tabela = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ", "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC")
    return texto.translate(tabela)


def classe_nossa(nome: str) -> str:
    chave = nome.strip().lower()
    for canonico, variantes in MAPA_CLASSES.items():
        if chave == canonico or chave in variantes:
            return canonico
    return chave


def confianca_minima(
    classe: str,
    padrao: float | None = None,
    por_classe: dict[str, float] | None = None,
) -> float:
    tabela = CONFIANCA_MINIMA_POR_CLASSE if por_classe is None else por_classe
    corte = CONFIANCA_MINIMA_OBSTACULO if padrao is None else padrao
    return tabela.get(classe_nossa(classe), corte)


