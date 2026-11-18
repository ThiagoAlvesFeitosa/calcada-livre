---
title: Calcada Livre
emoji: 🚶
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# FIAP Calçada Livre

Mapa colaborativo de acessibilidade das calçadas, feito com vídeo de celular e visão computacional.
Projeto da Global Solution 2 (2026.2) da FIAP, tema CitizenTech.

Qualquer pessoa abre o site, grava a calçada enquanto caminha e envia, sem instalar aplicativo.
O sistema encontra os obstáculos, dá uma nota de 0 a 100 para cada trecho e mostra o resultado
num mapa. A prefeitura recebe a lista das barreiras mais urgentes.

Piloto: Marília (SP).

Referências: Sidewalk AI Scanner (MIT Senseable City Lab) e Project Sidewalk (Universidade de
Washington).

Documentação em [`docs/`](docs/). Antes de programar, leia o [`AGENTS.md`](AGENTS.md).

Autor: Thiago Alves Feitosa — Sistemas de Informação, FIAP.

## No computador

```
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

No celular, na mesma Wi-Fi: `http://IP-DO-COMPUTADOR:8000` (gravar) e
`http://IP-DO-COMPUTADOR:8000/painel` (mapa). Na rede local o endereço é http: o GPS do navegador
em geral não libera. No Space o endereço é https: o GPS funciona.

## Publicar no Hugging Face Space

O token fica **só neste computador**. Não cole em `.env`, não suba para o GitHub.

1. Crie a conta em [huggingface.co](https://huggingface.co).
2. **New Space** → SDK **Docker** → hardware **CPU basic (grátis)** → público. Exemplo de nome:
   `calcada-livre`.
3. Em *Settings → Access Tokens*, crie um token com permissão **write**.
4. No PowerShell, uma vez: `huggingface-cli login` e cole o token (ele grava na sua pasta de
   usuário, fora do repositório). Se o comando não existir: `uv tool install huggingface_hub`.
5. Ligue o Space como segundo remoto (troque `SEU_USUARIO` e o nome do Space):

   ```
   git remote add space https://huggingface.co/spaces/SEU_USUARIO/calcada-livre
   git push space main
   ```

   Se pedir senha: usuário do Hugging Face + o **token** (não a senha da conta).
6. No site do Space, espere o build (PyTorch CPU + download dos pesos: vários minutos). Status
   **Running**.
7. Abra `https://huggingface.co/spaces/SEU_USUARIO/calcada-livre` no celular: **Usar minha
   localização**, enviar um vídeo, abrir o mapa e ver o trecho colorido.

O GitHub continua com `git push origin`. Depois de cada alteração aprovada: `git push origin` e
`git push space main`.

Não crie variável `HF_TOKEN` no repositório. Se o Space precisar de alguma variável, use
*Settings → Variables* na tela do Space.

CLIP, `lap` e `ftfy` já estão no `pyproject.toml`, para o YOLO-World não tentar instalar pacote
na hora de detectar. Os pesos (SegFormer, YOLO-World, CLIP) entram na **imagem** no `docker build`
(`scripts/baixar_modelos.py`). Continuam fora do Git.

Quando o Space gratuito reinicia, as notas e os quadros somem (pasta `saida/` no disco do
container). Os pesos na imagem não precisam baixar de novo. Ver ADR-006.

Se o envio cair perto de **60 segundos** (tempo esgotado), avise: aí o POST passa a devolver um
código na hora e a página pergunta o andamento a cada 3 segundos. Primeiro teste como está.
