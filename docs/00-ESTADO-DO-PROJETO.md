# Estado do projeto — FIAP Calçada Livre

Ponto de retomada de cada sessão. A entrada mais nova fica no topo.

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
