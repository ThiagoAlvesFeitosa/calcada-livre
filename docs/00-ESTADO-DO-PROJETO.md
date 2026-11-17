# Estado do projeto — FIAP Calçada Livre

Ponto de retomada de cada sessão. A entrada mais nova fica no topo.

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
