from pathlib import Path

import cv2
import numpy as np
import struct

from app.visao.pipeline import extrair_quadros


def _gravar_paisagem_com_rotacao(caminho: Path, graus: int) -> None:
    largura, altura = 80, 40
    escritor = cv2.VideoWriter(
        str(caminho),
        cv2.VideoWriter_fourcc(*"mp4v"),
        10.0,
        (largura, altura),
    )
    quadro = np.zeros((altura, largura, 3), dtype=np.uint8)
    quadro[:, : largura // 2] = (0, 0, 255)
    quadro[:, largura // 2 :] = (255, 0, 0)
    for _ in range(10):
        escritor.write(quadro)
    escritor.release()

    dados = bytearray(caminho.read_bytes())
    nome = dados.find(b"tkhd")
    assert nome >= 4
    matriz = nome + 4 + 40

    def fixo16(valor: float) -> bytes:
        return struct.pack(">i", int(round(valor * 65536)))

    def fixo230(valor: float) -> bytes:
        return struct.pack(">i", int(round(valor * (1 << 30))))

    if graus == 90:
        packed = (
            fixo16(0)
            + fixo16(1)
            + fixo230(0)
            + fixo16(-1)
            + fixo16(0)
            + fixo230(0)
            + fixo16(0)
            + fixo16(0)
            + fixo230(1)
        )
    else:
        raise ValueError(graus)
    dados[matriz : matriz + 36] = packed
    caminho.write_bytes(dados)


def test_video_em_pe_com_rotacao_gravada_chega_em_pe(tmp_path: Path) -> None:
    # preparar
    caminho = tmp_path / "celular-em-pe.mp4"
    _gravar_paisagem_com_rotacao(caminho, graus=90)

    # executar
    quadros = extrair_quadros(caminho, por_segundo=10)

    # verificar
    assert len(quadros) >= 1
    altura, largura = quadros[0][0].shape[:2]
    assert altura > largura
