import json
from pathlib import Path

from app.nota.regras import calcular_nota
from app.visao.pipeline import filtrar_obstaculos

RAIZ = Path(__file__).resolve().parents[2]
BRUTAS_CELULAR = RAIZ / "saida" / "5d4bd12a8ed04519bff6b7579fdca2bc" / "deteccoes_brutas.json"


def _deteccao(
    classe: str,
    *,
    altura: int,
    largura: int,
    y2: int,
    y1: int = 10,
    x1: int = 10,
    x2: int = 40,
    instante_s: float = 1.0,
    confianca: float = 0.4,
    na_calcada: bool = True,
) -> dict:
    return {
        "classe": classe,
        "confianca": confianca,
        "instante_s": instante_s,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "id_rastreio": None,
        "altura_quadro": altura,
        "largura_quadro": largura,
        "na_calcada": na_calcada,
        "topo_na_calcada": True,
        "largura_calcada_na_linha": largura,
    }


def test_retrato_entulho_conta_na_faixa_075_e_poste_nao() -> None:
    # preparar: altura 1920, 0,65 começa em y=672 e 0,75 em y=480
    entulho = _deteccao("construction debris", altura=1920, largura=1080, y2=500)
    poste = _deteccao("pole", altura=1920, largura=1080, y2=500, x1=50, x2=80)

    # executar
    resultado = filtrar_obstaculos([entulho, poste])

    # verificar
    assert [item["classe"] for item in resultado["obstaculos"]] == ["construction debris"]


def test_paisagem_nao_usa_faixa_075_no_chao() -> None:
    # preparar: 576 de altura, 0,65 exige y>=202; 0,75 aceitaria y>=144
    entulho = _deteccao("construction debris", altura=576, largura=1024, y2=180)

    # executar
    resultado = filtrar_obstaculos([entulho])

    # verificar
    assert resultado["obstaculos"] == []


def test_junta_entulho_e_caixa_proximos_com_sobreposicao() -> None:
    # preparar
    entulho = _deteccao(
        "construction debris",
        altura=1920,
        largura=1080,
        y1=800,
        y2=1100,
        x1=100,
        x2=400,
        instante_s=1.0,
    )
    caixa = _deteccao(
        "cardboard box",
        altura=1920,
        largura=1080,
        y1=850,
        y2=1150,
        x1=150,
        x2=450,
        instante_s=2.0,
    )

    # executar
    resultado = filtrar_obstaculos([entulho, caixa])

    # verificar
    assert len(resultado["obstaculos"]) == 1
    assert resultado["obstaculos"][0]["classe"] == "construction debris"


def test_nao_junta_poste_com_entulho_mesmo_sobrepostos() -> None:
    # preparar
    entulho = _deteccao(
        "construction debris",
        altura=1920,
        largura=1080,
        y1=800,
        y2=1100,
        x1=100,
        x2=400,
        instante_s=1.0,
    )
    poste = _deteccao(
        "pole",
        altura=1920,
        largura=1080,
        y1=800,
        y2=1100,
        x1=120,
        x2=380,
        instante_s=1.2,
    )

    # executar
    resultado = filtrar_obstaculos([entulho, poste])

    # verificar
    classes = sorted(item["classe"] for item in resultado["obstaculos"])
    assert classes == ["construction debris", "pole"]


def test_video_celular_vira_um_entulho_e_nota_28() -> None:
    # preparar
    assert BRUTAS_CELULAR.exists()
    deteccoes = json.loads(BRUTAS_CELULAR.read_text(encoding="utf-8"))["deteccoes"]

    # executar
    filtrado = filtrar_obstaculos(deteccoes)
    nota = calcular_nota(filtrado["obstaculos"], comprimento_m=11.18)

    # verificar
    assert [item["classe"] for item in filtrado["obstaculos"]] == ["construction debris"]
    assert nota["nota"] == 28
    assert nota["cor"] == "vermelho"
    assert nota["resumo_obstaculos"] == "1 problema: entulho"
