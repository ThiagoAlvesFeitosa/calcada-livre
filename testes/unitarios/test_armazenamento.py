from pathlib import Path

from app.adaptadores.armazenamento_falso import ArmazenamentoFalso


def test_guardar_trecho_nao_inclui_video_bruto(tmp_path: Path) -> None:
    # preparar
    pasta = tmp_path / "trecho"
    pasta.mkdir()
    (pasta / "resultado.json").write_text('{"obstaculos": []}', encoding="utf-8")
    (pasta / "nota.json").write_text('{"nota": 100}', encoding="utf-8")
    (pasta / "video.mp4").write_bytes(b"nao-e-para-subir")
    quadros = pasta / "quadros"
    quadros.mkdir()
    (quadros / "0000_0.0s.png").write_bytes(b"png")
    armazenamento = ArmazenamentoFalso()

    # executar
    armazenamento.guardar_trecho("trecho-01", pasta)

    # verificar
    assert armazenamento.ler_json("trecho-01", "resultado.json") == {"obstaculos": []}
    assert armazenamento.ler_json("trecho-01", "nota.json") == {"nota": 100}
    assert armazenamento.ler_quadro("trecho-01", "0000_0.0s.png") == b"png"
    assert not any(chave.endswith(".mp4") for chave in armazenamento.arquivos)
