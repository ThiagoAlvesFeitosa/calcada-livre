QUADROS_POR_SEGUNDO = 2

PIXELS_DILATACAO_CALCADA = 24

CONFIANCA_MINIMA_OBSTACULO = 0.25
CONFIANCA_MINIMA_PRIVACIDADE = 0.08
CONFIANCA_MINIMA_POR_CLASSE: dict[str, float] = {}

FRACAO_INFERIOR_VEICULO = 0.55
FRACAO_CAMINHO_INFERIOR = 0.45

SEGUNDOS_PARA_JUNTAR_MESMA_CLASSE = 1.5
SEGUNDOS_TOLERANCIA_GABARITO = 2.0

TAMANHO_DESFOQUE = 21

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


def confianca_minima(classe: str) -> float:
    return CONFIANCA_MINIMA_POR_CLASSE.get(classe_nossa(classe), CONFIANCA_MINIMA_OBSTACULO)


