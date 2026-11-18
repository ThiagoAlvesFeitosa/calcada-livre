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

Na mesma Wi-Fi: `http://IP-DO-COMPUTADOR:8000` (gravar) e
`http://IP-DO-COMPUTADOR:8000/painel` (mapa). Em http o GPS em geral não libera.

## Link público (Cloudflare Tunnel)

A visão roda neste computador. O celular usa um endereço **https** (GPS funciona). Resultados
ficam no Supabase. O Dockerfile permanece no repositório para um dia na Azure (ADR-006).

1. Copie `.env.example` para `.env` e preencha (não suba o `.env` para o Git):
   `ARMAZENAMENTO=supabase`, `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_BUCKET`.
   Vídeo no máximo **95 MB**; grave **até 30 segundos**.
2. No Supabase: crie um bucket **privado** com o mesmo nome de `SUPABASE_BUCKET`.
3. Suba o que já está em `saida/` (trechos 01 e 02), para o mapa não ficar cinza:

   ```
   uv run python scripts/subir_existentes.py
   ```

4. Instale o túnel no Windows:

   ```
   winget install Cloudflare.cloudflared
   ```

5. Com a API já no ar, em outro PowerShell:

   ```
   cloudflared tunnel --url http://127.0.0.1:8000
   ```

6. Abra no celular o **https** que o comando imprimir. O computador não pode dormir. Cada vez
   que você roda o comando, o link muda.

O POST devolve um código na hora e a página pergunta o andamento a cada 3 segundos (o túnel
corta respostas longas). Só um vídeo é processado por vez; o próximo espera.

Chaves só no `.env` neste computador. O navegador nunca recebe a chave do Supabase.
