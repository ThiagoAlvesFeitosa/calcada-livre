import json
from pathlib import Path

from app.adaptadores.armazenamento_falso import ArmazenamentoFalso
from app.trechos.recalcular import recalcular_trecho


def test_recalcula_nota_pelas_brutas_sem_video(tmp_path: Path) -> None:
    # preparar
    trecho_id = "trecho-teste"
    pasta = tmp_path / trecho_id
    pasta.mkdir()
    (pasta / "deteccoes_brutas.json").write_text(
        json.dumps(
            {
                "deteccoes": [
                    {
                        "classe": "construction debris",
                        "confianca": 0.2224,
                        "instante_s": 0.0,
                        "x1": 322,
                        "y1": 449,
                        "x2": 626,
                        "y2": 616,
                        "id_rastreio": None,
                        "altura_quadro": 1920,
                        "largura_quadro": 1080,
                        "na_calcada": True,
                        "topo_na_calcada": True,
                        "largura_calcada_na_linha": 828,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (pasta / "resultado.json").write_text(
        json.dumps({"obstaculos": [], "duracao_s": 4.58}),
        encoding="utf-8",
    )
    (pasta / "nota.json").write_text(
        json.dumps(
            {
                "nota": 100,
                "cor": "verde",
                "comprimento_m": 11.18,
                "comprimento_origem": "gps",
            }
        ),
        encoding="utf-8",
    )
    armazenamento = ArmazenamentoFalso()

    # executar
    saida = recalcular_trecho(trecho_id, tmp_path, armazenamento)

    # verificar
    assert saida["nota_antiga"]["nota"] == 100
    assert saida["nota_nova"]["nota"] == 28
    assert saida["nota_nova"]["cor"] == "vermelho"
    gravada = json.loads((pasta / "nota.json").read_text(encoding="utf-8"))
    assert gravada["nota"] == 28
    resultado = json.loads((pasta / "resultado.json").read_text(encoding="utf-8"))
    assert [item["classe"] for item in resultado["obstaculos"]] == ["construction debris"]
    assert resultado["duracao_s"] == 4.58
    assert armazenamento.ler_json(trecho_id, "nota.json")["nota"] == 28
