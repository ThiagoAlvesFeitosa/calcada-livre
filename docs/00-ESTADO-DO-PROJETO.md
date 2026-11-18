# Estado do projeto — FIAP Calçada Livre

Ponto de retomada de cada sessão. A entrada mais nova fica no topo.

## Situação em 18/11/2026 — layout gravar e mapa

Topo azul com “FIAP Calçada Livre”, abas Gravar/Mapa. Gravar: câmera no centro, botão fixo embaixo
(56 px). Fluxo GPS → “Você está em…” → Confirmar/Mudar endereço → dica → Abrir câmera → nota +
Ver no mapa. Mapa só com trechos filmados (linha 8 px), pontos vermelhos pelo instante do vídeo,
ficha por baixo, sem Censo. `duracao_s` no resultado.json. Commit só com o Thiago.

## Situação em 18/11/2026 — ajuste de tela (gravar e painel)

Gravar: primeira tela só título, frase e botão grande com ícone de câmera (SVG no HTML). Ao
tocar, pede GPS. Trecho até 50 m em destaque, Confirmar / Mudar endereço. Sem GPS ou longe:
“Não achamos um trecho cadastrado perto de você” e a lista. Depois da confirmação: uma linha de
dica e o botão da câmera. Paleta em variáveis CSS (`#1F4E79`, `#F2B705`, `#F7F6F2`…). Verde,
amarelo e vermelho só nas notas. Botões ≥ 48 px, fonte 18 px. Commit da F2.1 já no GitHub
(`dd10716`). Este ajuste de tela: commit só com o Thiago.

## Situação em 18/11/2026 — F2.1 caminho B (túnel + Supabase)

Hugging Face Docker ficou pago. A visão roda no computador; o celular entra pelo Cloudflare
Tunnel (https); notas e quadros com mosaico vão para um bucket privado no Supabase. Vídeo bruto
não sobe. Chaves só no `.env`. Painel lê pelo servidor. POST devolve código na hora; a página
pergunta a cada 3 s. Uma trava: um vídeo por vez. Limite 95 MB; tutorial 30 s. Script
`scripts/subir_existentes.py` para os trechos já em `saida/`. ADR-006 atualizado; Dockerfile
fica para a Azure. `uv run pytest`: 31 testes. Commit: `F2.1: tunel Cloudflare e Supabase`.

Próximo passo: `cloudflared tunnel --url http://127.0.0.1:8000` e teste no celular. Depois F2.2
se o prazo deixar.

## Situação em 18/11/2026 — F2.1 Space Docker (disco local)

Site público num Hugging Face Space **Docker**, CPU grátis, porta **7860**. `Dockerfile`: Python
3.11, uv 0.12.3, PyTorch só CPU, `libglib2.0-0` / `libgomp1` / `libgl1` / git para o OpenCV e o
CLIP. Um `RUN` executa `scripts/baixar_modelos.py` (SegFormer + YOLO-World + CLIP) para os pesos
ficarem **na imagem**, não no Git. Cabeçalho YAML no `README.md`. CLIP, `lap` e `ftfy` já estavam
no `pyproject.toml`.

**ADR-006:** armazenamento continua `saida/` no disco do Space. Motivo: prazo. Consequência: notas
e fotos somem quando o Space reinicia; os pesos na imagem não. Supabase e o teste de trocar o
adaptador ficam para depois. Token do Hugging Face só no computador (login da CLI), nunca em
arquivo do repositório.

Envio ainda é o POST sincrônico. Se o Space cortar perto de 60 s, aí sim processamento em segundo
plano. `uv run pytest`: 26 testes. Commit só com o Thiago; mensagem prevista:
`F2.1: Space Docker com pesos na imagem`.

Próximo passo: Thiago cria o Space, `git push space main`, testa no celular (https, GPS, vídeo,
mapa). Depois F2.2 (prioridade e laudo), se o prazo deixar.

## Situação em 18/11/2026 — GPS, data BR e nomes em português

A página de gravar não tem mais mapa. Botão **Usar minha localização** (até 50 m da linha);
confirmação com “escolher outro”. Sem GPS (http na rede local) ou longe: lista de nomes.
Testes: ponto no trecho 02 escolhe o 02; ponto em São Paulo não escolhe ninguém.

Data no painel: `dd/mm/aaaa HH:MM` no horário de Brasília. Classes em português no painel e nas
etiquetas dos quadros (`NOMES_CLASSES_PT` em `app/nota/parametros.py`). Os dois vídeos foram
processados de novo (`poste`, `caixa de papelao`, etc.). `uv run pytest`: 26 testes.

Commit: `ajuste: GPS, data BR e nomes em portugues`.

## Situação em 18/11/2026 — F1.3 painel com mapa

`http://IP:8000/painel`: Leaflet + OSM. Trechos 01 verde (100) e 02 vermelho (0); faces extras
cinza. Clique no 02 mostra nota, obstáculos por tipo e 3 quadros com mosaico. Cartão do Censo:
**1 de 2** filmados sem obstáculo no caminho, ao lado de **46,4%** (referência; não é a mesma
medida). `GET /trechos` devolve GeoJSON com a nota (calculada na hora se só houver resultado.json).
`uv run pytest`: 24 testes. GeoJSON ainda provisório (Av. Ipiranga); trocar pelo desenho do
quarteirão no geojson.io.

Próximo passo: F2.1 (nuvem), depois de gravar o vídeo da demo se o prazo apertar.

## Situação em 18/11/2026 — F1.2 envio pelo site

Site: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`. No celular da mesma Wi-Fi:
`http://IP:8000`. Sem https.

`POST /videos` recusa arquivo que não é vídeo, arquivo acima de 200 MB e trecho que não existe no
GeoJSON. O bruto é apagado depois. O `DetectorReal` carrega na primeira chamada e reaproveita.
Comprimento vem da linha em `dados/trechos.geojson`. Se só existir `resultado.json`, a nota é
calculada na hora. Quadros só em `saida/<id>/quadros/*.png` se o id estiver no GeoJSON; `..` → 404.

`uv run pytest` na fatia de envio: testes de vídeo passando. Próximo: F1.3 (painel com mapa).

## Situação em 18/11/2026 — F1.1 nota por trecho

A nota sai de 100, desconta 15 se `ocupacao_faixa` > 0,5, 8 se for parcial e 10 se for buraco ou
degrau. O desconto é ajustado para 100 m (trecho mais curto pesa mais). Piso 0. Verde ≥ 80,
amarelo 50–79, vermelho < 50. Tudo em `app/nota/parametros.py`. Os seis testes da F1.1 foram
escritos antes do código e passam. `uv run pytest`: 18 testes.

Comprimento provisório (duração do vídeo a passo normal; na F1.3 troca pelo medido no mapa):
trecho 01 = 10 m, trecho 02 = 30 m.

`uv run python scripts/nota.py`:

| Trecho | Comprimento | Nota | Cor | Obstáculos / 100 m | Faixa livre média |
| --- | --- | --- | --- | --- | --- |
| 01 | 10 m | 100 | verde | 0,0 | 100% |
| 02 | 30 m | 0 | vermelho | 33,3 | 83% |

No 02 nenhum obstáculo passou de 0,5 de ocupação (todos descontam como parcial). São 10 itens em
30 m, o que estoura o piso. Quando o comprimento real entrar na F1.3, a nota sobe se o trecho for
mais longo.

Commit: `F1.1: nota por trecho com testes`.

Próximo passo: F1.2 (envio pelo site).

## Situação em 18/11/2026 — calibração 0,12/65% e privacidade reforçada

Parâmetros finais da visão: confiança 0,12, recorte do caminho 65%. Privacidade: mosaico
(pixelização proporcional à caixa) em pessoas, placas e **todo** carro/moto, mais 80% da altura
da caixa para baixo — a caixa do modelo costuma parar acima da placa. Caixas de obstáculo com
linha de 3 px e texto maior. `uv run pytest`: 12 testes, inclusive carro com “placa” no lugar
errado ainda saindo com a faixa de baixo pixelizada.

Os dois trechos foram processados de novo. No 10,0 s e no 19,0 s a placa não dá para ler. No 5,0 s
as caixas da caixa de papelão e do pilar aparecem nítidas. Trecho 01 continua sem obstáculo na
lista.

Próximo passo: F1.1 (nota por trecho).

## Situação em 18/11/2026 — varredura de confiança e recorte

Commit anterior: `ajuste: avaliador e recorte do caminho`. O `processar.py` agora grava
`deteccoes_brutas.json` (confiança a partir de 0,05, dentro e fora do caminho). Dá para refiltrar
sem rodar os modelos. Entulho, areia e tijolo aceitam corte por classe
(`CONFIANCA_MINIMA_POR_CLASSE`). `scripts/varrer_filtros.py` testou 6 limiares × 3 recortes nos
dois trechos. `uv run pytest`: 11 testes.

Critério: mais acertos por posição no trecho 02, no máximo 1 falso positivo no trecho 01.

| conf | recorte | acertos 02 | FP 02 | prec. 02 | rev. 02 | FP 01 |
| --- | --- | --- | --- | --- | --- | --- |
| 0,10 | 45% | 6 | 0 | 100% | 67% | 0 |
| 0,10 | 55% | 7 | 1 | 88% | 78% | 0 |
| 0,10 | 65% | 9 | 3 | 75% | 100% | 0 |
| 0,12 | 45% | 5 | 0 | 100% | 56% | 0 |
| 0,12 | 55% | 7 | 0 | 100% | 78% | 0 |
| **0,12** | **65%** | **9** | **1** | **90%** | **100%** | **0** |
| 0,15 | 45% | 2 | 0 | 100% | 22% | 0 |
| 0,15 | 55% | 4 | 0 | 100% | 44% | 0 |
| 0,15 | 65% | 6 | 0 | 100% | 67% | 0 |
| 0,18 | 45% | 2 | 0 | 100% | 22% | 0 |
| 0,18 | 55% | 3 | 0 | 100% | 33% | 0 |
| 0,18 | 65% | 6 | 0 | 100% | 67% | 0 |
| 0,20 | 45% | 2 | 0 | 100% | 22% | 0 |
| 0,20 | 55% | 3 | 0 | 100% | 33% | 0 |
| 0,20 | 65% | 5 | 0 | 100% | 56% | 0 |
| 0,25 | 45% | 1 | 0 | 100% | 11% | 0 |
| 0,25 | 55% | 2 | 0 | 100% | 22% | 0 |
| 0,25 | 65% | 3 | 0 | 100% | 33% | 0 |
| 0,12 + entulho/areia 0,05 | 65% | 9 | 2 | 82% | 100% | 0 |

**Fica confiança 0,12 e recorte 65%.** Os 9 obstáculos do trecho 02 aparecem por posição (4 com a
classe certa); 1 falso positivo no 02; trecho 01 continua zerado. Baixar só entulho/areia para 0,05
não melhorou (mais um FP no 02). `CONFIANCA_MINIMA_POR_CLASSE` fica vazio.

Como varrer de novo: `uv run python scripts/varrer_filtros.py`.

Incluído no commit de calibração e privacidade.

Próximo passo: F1.1 (nota por trecho).

## Situação em 18/11/2026 — ajuste da visão (caminho + avaliador)

F0.2 já está no GitHub (`14a883e`). Esta rodada (cerca de 1 h) acrescentou `dados/gabarito.json`,
`scripts/avaliar.py` (acertos por posição, com qualquer classe, e acertos com a classe certa;
casamento ±2 s, uma marcação para um item) e o recorte do **caminho**: só conta obstáculo cuja base
está nos 45% de baixo do quadro. `ocupacao_faixa` usa a largura dessa faixa, não a máscara inteira.
Confiança mínima de obstáculo 0,25; `bench` e `sign` saíram da lista. `uv run pytest`: 9 testes.

Rodada s vs m (CPU), mesmos filtros:

| Modelo | Trecho | Marcações | Acertos posição | Acertos classe | FP | Prec. pos. | Rev. pos. | Tempo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| yolov8s | 02 | 1 | 1 | 1 | 0 | 100% | 11% | 1 min |
| yolov8s | 01 | 0 | — | — | 0 | — | — | 24 s |
| yolov8m | 02 | 1 | 1 | 1 | 0 | 100% | 11% | 1 min 10 s |
| yolov8m | 01 | 0 | — | — | 0 | — | — | 26 s |

Os dois modelos acharam só a caixa de papelão no 02 e zeraram o 01 (controle limpo). **Fica o s**
(`ARQUIVO_YOLO_WORLD = yolov8s-worldv2.pt`): mesmo resultado, um pouco mais rápido. O m não recuperou
entulho, areia nem o pilar com confiança 0,25. Revocação 1/9: o caminho e o limiar cortaram falsos
positivos e também os acertos fracos da F0.2. Plano B (Roboflow / treino em Marília) continua
necessário se a demo precisar dos 9 obstáculos.

Como avaliar: `uv run python scripts/avaliar.py saida/<id>/resultado.json`.

Commit feito: `ajuste: avaliador e recorte do caminho`.

Próximo passo: F1.1 (nota por trecho), usando `ocupacao_faixa` do caminho.

## Situação em 17/11/2026 — F0.2 pipeline de visão

O comando `uv run python scripts/processar.py ../videos/marilia_2026-11-17_trecho-02.mp4` gera
`saida/<id>/quadros/` (já com pessoas/placas borradas) e `saida/<id>/resultado.json`. No fim imprime
a lista com instante, confiança e `ocupacao_faixa`, e o tempo total (~55 s no CPU deste computador).
`uv run pytest`: 5 testes passando (F0.1 + três da visão com detector falso). PyTorch `2.15.0+cpu`.
Pesos em `modelos/` (fora do Git).

Decisões: números da visão em `app/visao/parametros.py`. O SegFormer do Cityscapes marca a calçada
de cimento de Marília quase toda como `road` (só dezenas de pixels como `sidewalk`); a máscara usa
as duas classes. Carro e moto não entram na lista de obstáculos (no vídeo estão na rua; com a
máscara de `road` a base deles cairia “na calçada”). O YOLO-World pequeno acerta pouco entulho e
areia; o rastreio ByteTrack sumia detecções fracas, então o script usa `predict` e junta a mesma
classe em até 1,5 s. Placa: se o modelo não achar, borra a faixa de baixo do veículo (55%).

Comparação com o gabarito no trecho 02 (9 obstáculos): o sistema listou 15 itens. Parece acertar
caixa de papelão (~1 s), lixeira (~5 s), pilar (~5 s) e alguns montes como `construction debris`
(3,5 s, 10,5 s, 19 s). Erra classe (banco no lugar de areia, ocupação 0,67), inventa lixeira/caixa
no começo e no fim, e não marca a árvore. Trecho 01 (controle, deveria ser zero) saiu com 10
marcações — muitos falsos positivos. Precisão ainda baixa; o plano B da arquitetura (Roboflow ou
treino em Marília) continua no radar.

Pendente: commit da F0.2 (aguardar o Thiago confirmar). Mensagem prevista:
`F0.2: pipeline de visão pela linha de comando`.

Próximo passo: F1.1 (nota por trecho, teste antes do código).

## Situação em 17/11/2026 — gabarito dos trechos

Não houve vistoria manual no local. O gabarito foi feito olhando os vídeos quadro a quadro e está
em `docs/gabarito-trechos.md`: trecho 01 sem obstáculo na faixa livre (controle) e trecho 02 com 9
obstáculos, 2 deles bloqueando mais da metade da calçada. Gravidade é estimativa visual, a confirmar
pelo Thiago. Sem vistoria cronometrada, não há comparação de tempo; se não der para refazer a pé, o
vídeo usa só precisão e revocação.

Spec Kit continua fora (ADR-005). Para a F0.2, usar o modo Plan do Cursor antes de programar.

## Situação em 17/11/2026 — F0.1 esqueleto caminhante

O projeto passou a ter pasta Python com `uv`, API FastAPI e o endereço `GET /saude`. Esse endereço
responde se a API está de pé e se o armazenamento consegue gravar e ler. Os testes usam um
armazenamento falso: um simula sucesso e o outro simula falha, sem acessar disco nem nuvem. Os dois
testes da fatia passam com `uv run pytest`.

Decisões: layout `app/` como no `AGENTS.md` (o `uv init` tinha criado `src/`, que foi descartado).
Armazenamento local grava um arquivo de prova em `saida/` e apaga em seguida. Supabase fica para a
F2.1.

Pendente: commit da F0.1 (aguardar o Thiago confirmar).

Próximo passo: F0.2 (processar o vídeo `trecho-02` pela linha de comando).

## Situação em 17/11/2026 — documentação inicial

Repositório criado no GitHub, ainda vazio. Esta pasta recebeu a documentação inicial: `README.md`,
`AGENTS.md`, `docs/05-arquitetura.md` (com ADR-001 a ADR-005), `docs/backlog.md` (F0.1 a F2.2),
duas regras do Cursor (`00-projeto` e `30-seguranca`), `.gitignore` e `.env.example`.

Decisões: trabalho individual; versão enxuta do método do OmniStay, sem PDF ABNT, porque a GS2 só
pede os links dos vídeos e o prazo é 19/11 (ADR-005).

Filmagem em 17/11: dois vídeos de calçada na R. Dom Pedro II, perto da R. Lima e Costa (bairro Boa
Vista, Marília), com 8 s e 26 s, recebidos pelo WhatsApp em 1024×576. Ficam fora do repositório, em
`../videos/`. Aparecem árvore na faixa, caixas de papelão, monte de areia com tijolos e monte de
brita sobre a calçada. Há placas de carro legíveis: precisam sair borradas.

Próximo passo: F0.1 (esqueleto caminhante), depois F0.2 com o vídeo `trecho-02`.

Pendente: anotações da vistoria manual do trecho (obstáculos e tempo), para medir a precisão.
