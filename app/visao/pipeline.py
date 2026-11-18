from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.portas.detector import Caixa, Detector
from app.visao.parametros import (
    CLASSES_FORA_DA_CONTAGEM,
    CONFIANCA_MINIMA_BRUTA,
    ESCALA_TEXTO_CAIXA,
    ESPESSURA_CAIXA,
    ESPESSURA_TEXTO_CAIXA,
    FRACAO_CAMINHO_INFERIOR,
    PIXELS_DILATACAO_CALCADA,
    QUADROS_POR_SEGUNDO,
    SEGUNDOS_PARA_JUNTAR_MESMA_CLASSE,
    classe_nossa,
    confianca_minima,
    etiqueta_quadro,
)
from app.visao.privacidade import borrar_pessoas_e_placas


@dataclass
class Obstaculo:
    classe: str
    confianca: float
    instante_s: float
    ocupacao_faixa: float
    id_rastreio: int | None
    instante_ultimo: float


def dilatar_mascara(mascara: np.ndarray, pixels: int = PIXELS_DILATACAO_CALCADA) -> np.ndarray:
    binaria = mascara.astype(bool)
    if pixels <= 0:
        return binaria
    nucleo = np.ones((2 * pixels + 1, 2 * pixels + 1), np.uint8)
    return cv2.dilate(binaria.astype(np.uint8), nucleo, iterations=1).astype(bool)


def _ponto_base(caixa: Caixa, altura: int, largura: int) -> tuple[int, int]:
    x_meio = min(max((int(caixa.x1) + int(caixa.x2)) // 2, 0), largura - 1)
    y_base = min(max(int(caixa.y2) - 1, 0), altura - 1)
    return x_meio, y_base


def base_na_calcada(caixa: Caixa, mascara: np.ndarray) -> bool:
    altura, largura = mascara.shape[:2]
    x_meio, y_base = _ponto_base(caixa, altura, largura)
    return bool(mascara[y_base, x_meio])


def mascara_caminho(mascara: np.ndarray, fracao_inferior: float = FRACAO_CAMINHO_INFERIOR) -> np.ndarray:
    caminho = mascara.astype(bool).copy()
    if caminho.size == 0:
        return caminho
    altura = caminho.shape[0]
    limite = int(altura * (1.0 - fracao_inferior))
    caminho[:limite, :] = False
    return caminho


def base_no_caminho(
    caixa: Caixa,
    mascara: np.ndarray,
    fracao_inferior: float = FRACAO_CAMINHO_INFERIOR,
) -> bool:
    return base_na_calcada(caixa, mascara_caminho(mascara, fracao_inferior))


def ocupacao_na_faixa(
    caixa: Caixa,
    mascara: np.ndarray,
    fracao_inferior: float = FRACAO_CAMINHO_INFERIOR,
) -> float:
    caminho = mascara_caminho(mascara, fracao_inferior)
    altura, largura = caminho.shape[:2]
    _, y_base = _ponto_base(caixa, altura, largura)
    x1 = min(max(int(caixa.x1), 0), largura)
    x2 = min(max(int(caixa.x2), 0), largura)
    largura_caixa = max(x2 - x1, 0)
    largura_caminho = int(np.count_nonzero(caminho[y_base]))
    if largura_caminho == 0:
        return 0.0
    return min(largura_caixa / largura_caminho, 1.0)


def _juntar(existentes: list[Obstaculo], novo: Obstaculo) -> None:
    for atual in existentes:
        mesmo_id = (
            novo.id_rastreio is not None
            and atual.id_rastreio is not None
            and novo.id_rastreio == atual.id_rastreio
        )
        mesma_classe = (
            atual.classe == novo.classe
            and abs(novo.instante_s - atual.instante_ultimo) <= SEGUNDOS_PARA_JUNTAR_MESMA_CLASSE
        )
        if mesmo_id or mesma_classe:
            atual.confianca = max(atual.confianca, novo.confianca)
            atual.ocupacao_faixa = max(atual.ocupacao_faixa, novo.ocupacao_faixa)
            atual.instante_ultimo = novo.instante_s
            if novo.id_rastreio is not None:
                atual.id_rastreio = novo.id_rastreio
            return
    existentes.append(novo)


def _eh_obstaculo(
    caixa: Caixa,
    padrao: float | None = None,
    por_classe: dict[str, float] | None = None,
) -> bool:
    classe = classe_nossa(caixa.classe)
    if classe in CLASSES_FORA_DA_CONTAGEM:
        return False
    return caixa.confianca >= confianca_minima(classe, padrao=padrao, por_classe=por_classe)


def _deteccao_no_caminho(deteccao: dict, fracao_inferior: float) -> bool:
    if not deteccao.get("na_calcada"):
        return False
    altura = int(deteccao["altura_quadro"])
    y_base = min(max(int(deteccao["y2"]) - 1, 0), altura - 1)
    limite = int(altura * (1.0 - fracao_inferior))
    return y_base >= limite


def _ocupacao_da_deteccao(deteccao: dict) -> float:
    largura_quadro = max(int(deteccao.get("largura_quadro", 0)), 1)
    x1 = min(max(int(deteccao["x1"]), 0), largura_quadro)
    x2 = min(max(int(deteccao["x2"]), 0), largura_quadro)
    largura_caixa = max(x2 - x1, 0)
    largura_caminho = int(deteccao.get("largura_calcada_na_linha", 0))
    if largura_caminho <= 0:
        return 0.0
    return min(largura_caixa / largura_caminho, 1.0)


def filtrar_obstaculos(
    deteccoes: list[dict],
    confianca_padrao: float | None = None,
    fracao_caminho: float | None = None,
    confianca_por_classe: dict[str, float] | None = None,
) -> dict:
    fracao = FRACAO_CAMINHO_INFERIOR if fracao_caminho is None else fracao_caminho
    obstaculos: list[Obstaculo] = []
    for item in deteccoes:
        caixa = Caixa(
            classe=classe_nossa(str(item["classe"])),
            confianca=float(item["confianca"]),
            x1=int(item["x1"]),
            y1=int(item["y1"]),
            x2=int(item["x2"]),
            y2=int(item["y2"]),
            id_rastreio=item.get("id_rastreio"),
        )
        if caixa.confianca < CONFIANCA_MINIMA_BRUTA:
            continue
        if not _eh_obstaculo(caixa, padrao=confianca_padrao, por_classe=confianca_por_classe):
            continue
        if not _deteccao_no_caminho(item, fracao):
            continue
        instante = float(item["instante_s"])
        _juntar(
            obstaculos,
            Obstaculo(
                classe=caixa.classe,
                confianca=caixa.confianca,
                instante_s=instante,
                ocupacao_faixa=_ocupacao_da_deteccao(item),
                id_rastreio=caixa.id_rastreio,
                instante_ultimo=instante,
            ),
        )
    return _serializar(obstaculos)


def _registro_bruto(caixa: Caixa, instante_s: float, mascara: np.ndarray) -> dict:
    altura, largura = mascara.shape[:2]
    x_meio, y_base = _ponto_base(caixa, altura, largura)
    return {
        "classe": classe_nossa(caixa.classe),
        "confianca": round(float(caixa.confianca), 4),
        "instante_s": round(float(instante_s), 2),
        "x1": int(caixa.x1),
        "y1": int(caixa.y1),
        "x2": int(caixa.x2),
        "y2": int(caixa.y2),
        "id_rastreio": caixa.id_rastreio,
        "altura_quadro": altura,
        "largura_quadro": largura,
        "na_calcada": bool(mascara[y_base, x_meio]),
        "largura_calcada_na_linha": int(np.count_nonzero(mascara[y_base])),
    }


def _anotar(quadro: np.ndarray, caixas: list[Caixa]) -> np.ndarray:
    anotado = quadro.copy()
    for caixa in caixas:
        cv2.rectangle(
            anotado,
            (int(caixa.x1), int(caixa.y1)),
            (int(caixa.x2), int(caixa.y2)),
            (40, 180, 40),
            ESPESSURA_CAIXA,
        )
        cv2.putText(
            anotado,
            etiqueta_quadro(caixa.classe),
            (int(caixa.x1), max(int(caixa.y1) - 8, 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            ESCALA_TEXTO_CAIXA,
            (40, 180, 40),
            ESPESSURA_TEXTO_CAIXA,
            cv2.LINE_AA,
        )
    return anotado


def _serializar(obstaculos: list[Obstaculo]) -> dict:
    return {
        "obstaculos": [
            {
                "classe": item.classe,
                "confianca": round(item.confianca, 4),
                "instante_s": round(item.instante_s, 2),
                "ocupacao_faixa": round(item.ocupacao_faixa, 4),
            }
            for item in obstaculos
        ]
    }


def processar_quadros(
    quadros: list[tuple[np.ndarray, float]],
    detector: Detector,
    pasta_saida: Path | str,
    identificador: str,
    duracao_s: float | None = None,
) -> dict:
    pasta = Path(pasta_saida) / identificador
    pasta_quadros = pasta / "quadros"
    pasta_quadros.mkdir(parents=True, exist_ok=True)
    brutas: list[dict] = []

    total = len(quadros)
    for indice, (quadro, instante_s) in enumerate(quadros):
        print(f"Quadro {indice + 1}/{total} ({instante_s:.1f} s)")
        analise = detector.analisar(quadro, instante_s)
        mascara = dilatar_mascara(analise.mascara_calcada)
        caixas = [
            Caixa(
                classe=classe_nossa(caixa.classe),
                confianca=caixa.confianca,
                x1=caixa.x1,
                y1=caixa.y1,
                x2=caixa.x2,
                y2=caixa.y2,
                id_rastreio=caixa.id_rastreio,
            )
            for caixa in analise.caixas
        ]
        for caixa in caixas:
            if caixa.confianca < CONFIANCA_MINIMA_BRUTA:
                continue
            brutas.append(_registro_bruto(caixa, instante_s, mascara))
        borrado = borrar_pessoas_e_placas(quadro, caixas)
        caixas_obstaculo = [
            caixa
            for caixa in caixas
            if _eh_obstaculo(caixa) and base_no_caminho(caixa, mascara)
        ]
        anotado = _anotar(borrado, caixas_obstaculo)
        nome = pasta_quadros / f"{indice:04d}_{instante_s:.1f}s.png"
        cv2.imwrite(str(nome), anotado)

    resultado = filtrar_obstaculos(brutas)
    if duracao_s is None:
        duracao_s = quadros[-1][1] if quadros else 0.0
    resultado["duracao_s"] = round(float(duracao_s), 2)
    (pasta / "resultado.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (pasta / "deteccoes_brutas.json").write_text(
        json.dumps({"deteccoes": brutas}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return resultado


def extrair_quadros(caminho_video: Path | str, por_segundo: int = QUADROS_POR_SEGUNDO) -> list[tuple[np.ndarray, float]]:
    captura = cv2.VideoCapture(str(caminho_video))
    if not captura.isOpened():
        raise FileNotFoundError(f"Não foi possível abrir o vídeo: {caminho_video}")
    fps = captura.get(cv2.CAP_PROP_FPS) or 30.0
    passo = max(int(round(fps / por_segundo)), 1)
    quadros: list[tuple[np.ndarray, float]] = []
    indice = 0
    while True:
        ok, quadro = captura.read()
        if not ok:
            break
        if indice % passo == 0:
            quadros.append((quadro, indice / fps))
        indice += 1
    captura.release()
    return quadros


def duracao_do_video(caminho_video: Path | str) -> float:
    captura = cv2.VideoCapture(str(caminho_video))
    if not captura.isOpened():
        return 0.0
    fps = captura.get(cv2.CAP_PROP_FPS) or 0.0
    quadros = captura.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    captura.release()
    if fps > 0 and quadros > 0:
        return float(quadros / fps)
    return 0.0


def processar_video(
    caminho_video: Path | str,
    detector: Detector,
    pasta_saida: Path | str,
    identificador: str | None = None,
) -> dict:
    caminho = Path(caminho_video)
    id_varredura = identificador or caminho.stem
    quadros = extrair_quadros(caminho)
    duracao = duracao_do_video(caminho)
    if duracao <= 0 and quadros:
        duracao = quadros[-1][1]
    return processar_quadros(quadros, detector, pasta_saida, id_varredura, duracao_s=duracao)
