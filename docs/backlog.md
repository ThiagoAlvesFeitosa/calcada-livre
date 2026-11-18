# Backlog — FIAP Calçada Livre

Fatias verticais, em ordem de dependência. A próxima é sempre a primeira cuja dependência já está
pronta. **Mínimo para gravar o vídeo: F0.1 a F1.3 rodando no computador.**

**Regra de pronto (versão enxuta, por causa do prazo):**

- a fatia funciona na demo com o vídeo de Marília;
- os testes da F1.1 (nota) e os critérios marcados com *(teste)* passam;
- nenhum número mágico: pesos, limites e intervalos ficam em `app/nota/parametros.py` ou no `.env`;
- nenhum dado pessoal em log, nenhum quadro salvo sem borrar pessoas e placas;
- um commit único e descritivo por fatia, por exemplo `F1.1: nota por trecho com testes`.

---

## Fase 0 — Fundação

## F0.1 — Esqueleto caminhante

**Objetivo:** provar que a estrutura inteira funciona antes de qualquer coisa difícil.

**Descrição:**
> O sistema responde se está de pé e se consegue gravar e ler no armazenamento configurado.

**Critérios de aceite:**

- `GET /saude` devolve `{"status": "ok", "armazenamento": "ok"}` *(teste)*
- Com armazenamento indisponível, devolve `armazenamento: "falha"` sem derrubar a API *(teste)*
- `uv run pytest` roda e passa

**Depende de:** nada.
**Referência:** `05-arquitetura.md`, seções 3.2 e 3.7.

## F0.2 — Processar um vídeo pela linha de comando

**Objetivo:** ver a visão computacional funcionando no vídeo real de Marília. É a fatia que não
pode faltar.

**Descrição:**
> Dado um vídeo de calçada, o sistema separa os quadros, marca onde é calçada, encontra o que está
> em cima dela e salva os quadros anotados, com pessoas e placas borradas, e um resumo em JSON.

**Critérios de aceite:**

- `uv run python scripts/processar.py videos/trecho.mp4` gera `saida/<id>/quadros/` e `saida/<id>/resultado.json`
- O JSON lista cada obstáculo uma vez, com classe, confiança e instante no vídeo
- Objeto cuja base não está sobre a calçada não conta como obstáculo *(teste, com detector falso)*
- Todo quadro salvo tem pessoas e placas borradas *(teste, com detector falso)*
- Mostra no fim quanto tempo levou

**Depende de:** F0.1.
**Referência:** `05-arquitetura.md`, seção 3.3.

---

## Fase 1 — Valor visível no computador

## F1.1 — Nota por trecho (teste antes do código)

**Objetivo:** transformar os obstáculos numa nota que a prefeitura e o cidadão entendam.

**Descrição:**
> Cada trecho recebe uma nota de 0 a 100, a quantidade de obstáculos por 100 metros, a faixa livre
> média e uma cor: verde, amarelo ou vermelho.

**Critérios de aceite (cada um vira um teste):**

- `test_trecho_sem_obstaculo_tem_nota_100`
- `test_obstaculo_que_bloqueia_mais_da_metade_desconta_mais_que_parcial`
- `test_buraco_e_degrau_descontam_como_barreira`
- `test_nota_nunca_fica_negativa`
- `test_nota_considera_comprimento_do_trecho`
- `test_cor_segue_limites_80_e_50`

**Depende de:** F0.2.
**Referência:** `05-arquitetura.md`, seção 3.4.

## F1.2 — Envio pelo site

**Objetivo:** o cidadão grava e envia sem instalar nada.

**Descrição:**
> Pelo navegador do celular, a pessoa vê um tutorial curto, escolhe o trecho no mapa, grava a
> calçada com a câmera do próprio celular e envia. Ao terminar o processamento, vê a nota do trecho.

**Critérios de aceite:**

- A página abre a câmera traseira pelo `<input type="file" accept="video/*" capture="environment">`
- `POST /videos` recusa arquivo que não é vídeo e arquivo acima do limite *(teste)*
- `POST /videos` recusa trecho que não existe *(teste)*
- O vídeo bruto é apagado depois do processamento *(teste)*
- Barra de progresso no envio e tela "processando"

**Depende de:** F1.1.
**Referência:** `05-arquitetura.md`, seções 3.1 e 3.2; ADR-001 e ADR-004.

## F1.3 — Painel com o mapa

**Objetivo:** ver o quarteirão de Marília colorido no mapa.

**Descrição:**
> O painel mostra os trechos coloridos pela nota. Ao clicar, aparecem a nota, os obstáculos por
> tipo, três quadros anotados e a data da varredura. Um cartão compara o quarteirão com o Censo
> 2022 de Marília (46,4% dos moradores em calçada desobstruída).

**Critérios de aceite:**

- `dados/trechos.geojson` com as faces do quarteirão filmado (desenhar no geojson.io)
- `GET /trechos` devolve GeoJSON com a nota mais recente de cada trecho *(teste)*
- Trecho nunca filmado aparece cinza, não verde
- Mapa com Leaflet e OpenStreetMap

**Depende de:** F1.2.
**Referência:** `05-arquitetura.md`, seção 3.6.

---

## Fase 2 — Nuvem e decisão

## F2.1 — Nuvem (Space Docker; disco local)

**Objetivo:** o site funcionando por um link público https (GPS no celular).

**Descrição:**
> O sistema roda num Hugging Face Space Docker, plano CPU grátis. Resultados ficam no disco do
> Space (`saida/`). Supabase fica para depois (ADR-006).

**Critérios de aceite:**

- `Dockerfile`: Python 3.11, uv, PyTorch só CPU, porta 7860; pacotes do OpenCV; um `RUN` baixa
  SegFormer, YOLO-World e CLIP para dentro da imagem
- Cabeçalho YAML do Space no `README.md` (`sdk: docker`, `app_port: 7860`)
- Pesos fora do Git (`modelos/`, `*.pt`)
- `git ls-files .env` volta vazio; o `.env.example` lista as variáveis; token do Hugging Face só
  no computador de quem publica
- No celular: abrir o https, usar o GPS, enviar um vídeo e ver o mapa colorido
- Se o envio cair perto de 60 s (tempo esgotado do Space), só então passar o POST para segundo
  plano com consulta a cada 3 s — primeiro testar como está

**Fora desta fatia:** adaptador Supabase e o teste “trocar `ARMAZENAMENTO` sem mudar código fora
do adaptador”.

**Depende de:** F1.3.
**Referência:** `05-arquitetura.md`, seção 3.7; ADR-003; ADR-006.

## F2.2 — Prioridade e laudo

**Objetivo:** ajudar o gestor a decidir o que consertar primeiro.

**Descrição:**
> As barreiras são ordenadas pela gravidade e pela proximidade de escola, posto de saúde ou ponto
> de ônibus. Cada trecho ganha um laudo curto em linguagem simples para o gestor e uma frase para
> o cidadão.

**Critérios de aceite:**

- `test_barreira_perto_de_escola_vem_antes_de_igual_longe` *(teste)*
- `test_sem_chave_de_llm_usa_laudo_de_modelo_fixo` *(teste)*
- `test_laudo_so_cita_obstaculos_que_existem_no_trecho` *(teste)*
- Aba "Gestor" no painel com a lista e o laudo

**Depende de:** F1.3.
**Referência:** `05-arquitetura.md`, seção 3.5.
