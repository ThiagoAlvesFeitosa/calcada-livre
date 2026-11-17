# AGENTS.md — leia antes de escrever qualquer linha

## O que é

FIAP Calçada Livre: o cidadão grava a calçada pelo navegador do celular, a visão computacional
encontra os obstáculos, cada trecho ganha uma nota de 0 a 100 e um mapa mostra o resultado. A
prefeitura recebe a lista de prioridades. Projeto da Global Solution 2 da FIAP, piloto em Marília.

Documentos: `docs/05-arquitetura.md` (como funciona e por quê) e `docs/backlog.md` (o que fazer,
em ordem). O estado atual está em `docs/00-ESTADO-DO-PROJETO.md`.

## Tecnologia

| Camada | Tecnologia |
| --- | --- |
| API | Python 3.11+, FastAPI, Pydantic |
| Visão | OpenCV, Hugging Face Transformers (SegFormer), Ultralytics (YOLO-World) |
| Páginas | HTML, CSS e JavaScript simples servidos pela FastAPI; Leaflet e OpenStreetMap |
| Armazenamento | Pasta `saida/` no computador; Supabase (Postgres + Storage) na nuvem |
| Nuvem | Hugging Face Spaces (Docker) |
| Testes | pytest |
| Dependências | uv |

## Estrutura

```
app/
├── main.py              entrada da API e rotas
├── config.py            configuração pelo .env
├── visao/               segmentacao.py, deteccao.py, pipeline.py, privacidade.py
├── nota/                regras.py, parametros.py
├── decisao/             prioridade.py, laudo.py
├── portas/              interfaces: armazenamento, detector, laudo
├── adaptadores/         implementações reais e falsas das interfaces
└── web/                 coleta.html, painel.html, estilos e scripts
scripts/processar.py     processa um vídeo pela linha de comando
dados/trechos.geojson    faces do quarteirão piloto
testes/                  unitarios/ e ponta_a_ponta/
docs/                    estado, arquitetura e backlog
```

## Regras

1. **Uma fatia por vez, na ordem do backlog.** Não comece a próxima antes de a atual estar pronta.
2. **Teste antes do código na nota (F1.1)** e nos critérios marcados com *(teste)*. Escreva o teste,
   veja falhar pelo motivo certo, implemente o mínimo, veja passar.
3. **Nenhum número mágico.** Pesos e limites da nota ficam em `app/nota/parametros.py`. Quadros por
   segundo, desfoque, dilatação, confiança e intervalos da visão ficam em `app/visao/parametros.py`.
   O resto vai no `.env`.
4. **Interfaces para o que é externo.** Armazenamento, detector e laudo têm implementação real e
   falsa. Teste nunca baixa modelo, nunca chama LLM e nunca acessa o Supabase.
5. **Privacidade.** Pessoas e placas borradas antes de salvar qualquer quadro. Vídeo bruto apagado
   depois do processamento. Nenhum dado pessoal em log.
6. **Segredos.** Nunca leia, mostre ou registre o conteúdo do `.env`. Variáveis novas entram no
   `.env.example`, sem valor.
7. **Git é do Thiago.** Não faça commit nem push sem ele confirmar. Um commit por fatia, com o código
   da fatia na mensagem: `F1.1: nota por trecho com testes`.
8. **Documentação errada não se contorna.** Se a arquitetura ou o backlog não baterem com o que o
   código precisa, aponte a diferença e proponha a correção antes de implementar.

## Ao fechar uma fatia

- Rode `uv run pytest`.
- Acrescente no topo de `docs/00-ESTADO-DO-PROJETO.md` o que a fatia fez, as decisões e o que ficou
  pendente.

## Nunca

- Subir vídeo real, quadro sem borrar ou `.env` para o repositório.
- Inventar obstáculo no laudo: ele só cita o que o detector encontrou no trecho.
- Mostrar trecho nunca filmado como verde.
- Adicionar Redis, Celery, fila externa ou framework de front-end: não cabe no prazo.
