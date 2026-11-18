# Arquitetura — FIAP Calçada Livre

Versão 1, 17/11/2026. Os documentos de processos, jornada, fluxo de dados e modelagem do método
completo ficaram de fora por causa do prazo (ADR-005). As tabelas estão na seção 3.4.

## 1. Visão geral

```
Celular (navegador)                Nuvem                                  Navegador
┌───────────────┐   vídeo +    ┌──────────────────────────────┐   GeoJSON   ┌──────────────┐
│ Site de coleta│ ───trecho──▶ │ API FastAPI (Hugging Face    │ ──────────▶ │ Painel (mapa)│
│ tutorial +    │              │ Space, Docker)               │             │ cidadão e    │
│ gravar/enviar │              │  ├ pipeline de visão         │             │ gestor       │
└───────────────┘              │  ├ cálculo da nota           │             └──────────────┘
                               │  └ prioridade e laudo (IA)   │
                               │ Supabase: Postgres + Storage │
                               └──────────────────────────────┘
```

## 2. As 4 tecnologias obrigatórias

| Exigência | Onde está | O que mostrar no vídeo |
| --- | --- | --- |
| Visão computacional | Segmentação da calçada (SegFormer, Cityscapes) e detecção de obstáculos (YOLO-World, por texto) | Quadro de Marília com a calçada pintada e caixas nos obstáculos |
| Análise de dados | Nota 0–100 por trecho, obstáculos por 100 m, faixa livre média, comparação com o Censo | Mapa colorido e números do quarteirão |
| Cloud | API e páginas no Hugging Face Spaces; vídeos e resultados no Supabase | Envio pelo celular e resultado no painel |
| Inteligência artificial | Modelos de visão, priorização das barreiras e laudo por LLM | Aba do gestor com prioridades e laudo |

## 3. Componentes

### 3.1 Site de coleta

- Página única para celular.
- Tutorial em 3 telas: celular deitado, na altura do peito, apontado para a calçada 3 a 5 m à
  frente; andar devagar e sem parar; um vídeo por face de quadra, até 60 s.
- Escolha do trecho num mapa (Leaflet + OpenStreetMap).
- Botão "Gravar": `<input type="file" accept="video/*" capture="environment">`.
- Barra de progresso e tela "processando".

### 3.2 API (FastAPI)

- `GET /saude` — se a API e o armazenamento respondem.
- `POST /videos` — recebe vídeo e `trecho_id`, processa, grava o resultado, apaga o vídeo bruto.
- `GET /trechos` — GeoJSON com a nota mais recente de cada trecho.
- `GET /trechos/{id}` — nota, obstáculos por tipo, quadros anotados, data, laudo.
- Processamento síncrono, porque o vídeo é curto. Fila fica no roadmap.

### 3.3 Pipeline de visão computacional

1. Extrair 2 quadros por segundo (OpenCV).
2. Máscara da calçada: SegFormer `nvidia/segformer-b0-finetuned-cityscapes-1024-1024`, classe
   `sidewalk`.
3. Objetos: YOLO-World (`yolov8s-worldv2.pt`) com as classes `pole`, `tree`, `trash bin`, `car`,
   `motorcycle`, `pothole`, `stairs`, `construction debris`, `sand pile`, `bricks`, `cardboard box`,
   `bench`, `sign`, `person`, `license plate`.
4. Obstáculo: caixa cuja base cai dentro da máscara da calçada.
5. Contar cada obstáculo uma vez: `model.track` (ByteTrack); cada ID único é um obstáculo.
6. Faixa livre (relativa): numa linha no terço de baixo do quadro, a fração da calçada não coberta
   por obstáculo. Não é medida em metros.
7. Privacidade: `person` e `license plate` borrados antes de salvar qualquer quadro.

Plano B, se o YOLO-World errar demais em Marília: modelo pronto do Roboflow Universe pela API
hospedada, ou rotular cerca de 100 quadros de Marília e treinar um YOLOv8n.

Rampa: o modelo por texto reconhece mal. Na demo, é marcada à mão; detecção de rampa (dataset
RampNet do Project Sidewalk) fica no roadmap.

### 3.4 Dados e nota

Tabelas:

- `trechos` (id, nome, geometria GeoJSON, comprimento_m)
- `varreduras` (id, trecho_id, data, duracao_s)
- `deteccoes` (id, varredura_id, classe, confianca, instante_s, bbox, caminho_quadro)
- `notas` (varredura_id, nota, obstaculos_por_100m, faixa_livre_media)

Regra inicial da nota (inspirada no AccessScore do Project Sidewalk, a calibrar). Os valores ficam
em `app/nota/parametros.py`:

- começa em 100;
- −15 por obstáculo que tira mais da metade da faixa livre;
- −8 por obstáculo parcial;
- −10 por buraco ou degrau;
- ajustada por 100 m de trecho; mínimo 0;
- verde ≥ 80, amarelo 50–79, vermelho < 50.

### 3.5 Prioridade e laudo

- Prioridade = gravidade × proximidade de escola, posto de saúde ou ponto de ônibus (pontos do
  OpenStreetMap, guardados em `dados/`).
- Laudo: LLM recebe o JSON do trecho e escreve um parágrafo para o gestor e uma frase para o
  cidadão. Sem chave, usa um texto de modelo fixo. O laudo só pode citar obstáculos que existem
  no trecho.

### 3.6 Painel

- Cidadão: mapa com trechos coloridos; ao clicar, nota, obstáculos por tipo, 3 quadros anotados e
  data. Trecho nunca filmado aparece cinza.
- Gestor: lista de prioridades com laudo; cartão com o Censo de Marília (46,4%).

### 3.7 Nuvem

- Hugging Face Spaces (Docker, CPU grátis): roda a API, os modelos e serve as páginas na porta 7860.
- Pesos do SegFormer, YOLO-World e CLIP entram na imagem no `docker build`; não vão para o Git.
- Nesta fatia o armazenamento no Space é a pasta `saida/` no disco do container (ADR-006).
- Supabase (Postgres + Storage) fica para depois; a interface de armazenamento continua pronta para
  essa troca.
- Detector (real ou falso para teste) e laudo (`llm`, `modelo_fixo` ou falso para teste) já são
  trocáveis.

## 4. Decisões (ADR)

### ADR-001 — Site em vez de aplicativo

**Contexto.** Quem colabora com o mapa não quer instalar nada para filmar uma rua.

**Decisão.** Tudo pelo navegador do celular, com a câmera aberta por `capture="environment"`.

**Alternativas.** Aplicativo Android/iOS; formulário com envio de arquivo pelo computador.

**Consequências.** *Aceitas:* sem GPS contínuo nem guia na tela durante a gravação. *Ganhas:*
nenhuma barreira de instalação; mesmo desenho do MIT.

### ADR-002 — Modelos prontos, sem treinar

**Contexto.** Dois dias de prazo e nenhum dataset de calçada brasileira.

**Decisão.** SegFormer treinado no Cityscapes para a calçada e YOLO-World com classes por texto
para os obstáculos.

**Alternativas.** Treinar YOLOv8 com o Project Sidewalk; rotular imagens de Marília.

**Consequências.** *Aceitas:* precisão menor e rampa fraca. *Ganhas:* demo funcionando no prazo;
o ajuste com Project Sidewalk e Marília vira o próximo passo do roadmap.

### ADR-003 — Hugging Face Spaces e Supabase

**Contexto.** Os modelos precisam de PyTorch e memória; o custo tem de ser zero.

**Decisão.** API e modelos num Space Docker; banco e arquivos no Supabase.

**Alternativas.** Render (plano grátis com pouca memória); Azure ou Google Cloud (exigem créditos).

**Consequências.** *Aceitas:* Space gratuito "dorme" sem uso e demora a acordar. *Ganhas:* custo
zero e troca fácil por outra nuvem, pela interface de armazenamento.

### ADR-004 — Vídeo bruto não fica guardado

**Contexto.** O vídeo da rua mostra pessoas e placas reais (LGPD).

**Decisão.** Guardar só quadros com pessoas e placas borradas e apagar o vídeo depois do
processamento. Vídeos reais nunca vão para o repositório.

**Alternativas.** Guardar o vídeo para reprocessar depois.

**Consequências.** *Aceitas:* para reprocessar, é preciso filmar de novo. *Ganhas:* nenhum dado
pessoal guardado.

### ADR-005 — Versão enxuta do método

**Contexto.** Trabalho individual e prazo em 19/11/2026.

**Decisão.** Só arquitetura, backlog, `AGENTS.md`, duas regras do Cursor e teste antes do código
na regra da nota. Sem Spec Kit, sem constituição e sem os documentos 01 a 04.

**Alternativas.** Método completo do OmniStay.

**Consequências.** *Aceitas:* menos garantia de qualidade fora da nota. *Ganhas:* demo pronta para
gravar na quarta.

### ADR-006 — Disco local no Space nesta fatia

**Contexto.** A F2.1 do backlog previa Supabase junto com o Space. O prazo da GS2 é curto; o
adaptador de nuvem ainda não está escrito.

**Decisão.** Publicar só o Space Docker (CPU grátis). Notas, quadros e JSON ficam em `saida/` no
disco do container. Pesos dos modelos vêm na imagem (baixados no `docker build`). O token do
Hugging Face fica só no computador de quem publica, nunca no repositório.

**Alternativas.** Implementar o adaptador Supabase agora (ADR-003 completo); volume `/data` pago
no Space.

**Consequências.** *Aceitas:* quando o Space gratuito reinicia, os resultados somem e o mapa volta
cinza até filmar de novo; os pesos na imagem não precisam baixar outra vez. *Ganhas:* link público
https (GPS no celular) no prazo, sem Redis, fila nem banco.

## 5. Fora da demo (roadmap)

- Rota acessível a pé (OSRM ou Valhalla com custo por barreira).
- Largura em metros e inclinação.
- Detector ajustado com Project Sidewalk e imagens de Marília; detecção de rampa.
- Trecho identificado pelo GPS do celular.
- Varreduras repetidas mostrando a evolução de cada trecho.
