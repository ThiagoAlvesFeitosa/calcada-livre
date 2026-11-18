QUADROS_POR_SEGUNDO = 2

PIXELS_DILATACAO_CALCADA = 24

CONFIANCA_MINIMA_OBSTACULO = 0.12
CONFIANCA_MINIMA_PRIVACIDADE = 0.08
CONFIANCA_MINIMA_BRUTA = 0.05
CONFIANCA_MINIMA_POR_CLASSE: dict[str, float] = {}
CONFIANCAS_VARREDURA = (0.10, 0.12, 0.15, 0.18, 0.20, 0.25)
FRACOES_CAMINHO_VARREDURA = (0.45, 0.55, 0.65)
CLASSES_CORTE_MENOR = ("construction debris", "sand pile", "bricks")

FRACAO_INFERIOR_VEICULO = 1.0
FRACAO_EXTENSAO_INFERIOR_VEICULO = 0.8
FRACAO_CAMINHO_INFERIOR = 0.65

SEGUNDOS_PARA_JUNTAR_MESMA_CLASSE = 1.5
SEGUNDOS_TOLERANCIA_GABARITO = 2.0

DIVISOES_MOSAICO = 8
PIXELS_MINIMOS_MOSAICO = 8
ESPESSURA_CAIXA = 3
ESCALA_TEXTO_CAIXA = 0.7
ESPESSURA_TEXTO_CAIXA = 2

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
    ],
    "sand pile": ["sand pile", "pile of sand", "gravel pile", "dirt pile"],
    "bricks": ["bricks"],
    "cardboard box": ["cardboard box", "cardboard boxes"],
    "bench": ["bench"],
    "sign": ["sign"],
    "person": ["person"],
    "license plate": ["license plate"],
}


def nomes_para_yolo() -> list[str]:
    nomes: list[str] = []
    for canonico, variantes in MAPA_CLASSES.items():
        if canonico in CLASSES_IGNORADAS:
            continue
        nomes.extend(variantes)
    return nomes


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


