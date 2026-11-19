# Gabarito dos trechos filmados — Marília, 17/11/2026

Contagem feita à mão, olhando os vídeos quadro a quadro (2 quadros por segundo). Serve para medir
a precisão do detector na F0.2: o que o sistema achou será comparado com esta lista.

Local: R. Dom Pedro II, perto da R. Lima e Costa (bairro Boa Vista), Marília (SP).
Os vídeos ficam fora do repositório, em `../videos/`.

Gravidade (estimativa visual, a confirmar pelo Thiago, que esteve no local):

- **bloqueio**: ocupa mais da metade da faixa livre;
- **parcial**: estreita a passagem, mas ainda dá para passar;
- **fora da faixa**: na faixa de serviço, junto ao meio-fio, sem estreitar a passagem.

Carros estacionados na rua não contam.

## Trecho 01 — `marilia_2026-11-17_trecho-01.mp4` (8 s)

Calçada larga, de pedra portuguesa. **Nenhum obstáculo na faixa livre.**

| # | Instante | Objeto | Gravidade |
| --- | --- | --- | --- |
| — | 5–8 s | Árvore jovem com mato no canteiro, junto ao meio-fio | fora da faixa |

Uso: trecho de controle. O detector não deve marcar obstáculo aqui. Qualquer marcação é falso
positivo.

## Trecho 02 — `marilia_2026-11-17_trecho-02.mp4` (26 s)

Calçada de cimento com obra em andamento. **9 obstáculos na faixa livre.**

| # | Instante | Objeto | Classe esperada | Gravidade |
| --- | --- | --- | --- | --- |
| 1 | 2–5 s | Árvore na calçada, junto às caixas | `tree` | parcial |
| 2 | 2–6 s | Duas caixas de papelão empilhadas | `cardboard box` | parcial |
| 3 | 4–7 s | Cesto de lixo suspenso num poste, com saco preto | `trash bin` | parcial |
| 4 | 6–10 s | Monte de entulho (caliça) junto ao muro | `construction debris` | bloqueio |
| 5 | 7–12 s | Pilar de concreto em forma de Y no meio da calçada | `pole` | parcial |
| 6 | 15–17 s | Entulho com madeira e cano junto ao muro, ao lado do portão | `construction debris` | parcial |
| 7 | 12–20 s | Monte grande de areia com tijolos e ripa de madeira | `sand pile` / `bricks` | bloqueio |
| 8 | 18–23 s | Monte de brita (o de trás) | `construction debris` | parcial |
| 9 | 19–24 s | Monte de brita (o da frente) | `construction debris` | parcial |

De 23 s até o fim, a calçada fica livre.

## Trecho 03 — `marilia_2026-11-19_trecho-03.mp4` (5 s)

Recorte de uma gravação de tela. Monte de madeira e galhos no caminho, encostado no muro,
do segundo 0 ao 5.

| # | Instante | Objeto | Classe esperada | Gravidade |
| --- | --- | --- | --- | --- |
| 1 | 0–5 s | Monte de madeira e galhos no caminho | `construction debris` | bloqueio |

O trecho-04 ainda não existe.

## Versões em pé (recorte 9:16)

Os vídeos 01 e 02 foram filmados deitado. Para medir o celular em pé, há recortes centrais 9:16 em
`saida/retrato/` (não vão para o Git), mesma linha do tempo.

Chaves no `dados/gabarito.json`: `marilia_2026-11-17_trecho-01-retrato` e
`...-trecho-02-retrato`. No 02, a lixeira (#3) e o entulho junto ao muro (#4) ficam **fora do
quadro** (centro da caixa caiu fora da faixa 9:16). Os outros 7 itens continuam valendo.

O trecho-03 já está em pé (gravação de tela).

Fora da contagem: tijolo com fita zebrada apoiado no meio-fio, do lado da rua (7–10 s e 19–22 s).

## Como medir na F0.2

- **Acertos**: obstáculo do gabarito que o sistema marcou, no instante certo (±2 s).
- **Falsos positivos**: marcação que não corresponde a nenhuma linha do gabarito (inclui qualquer
  marcação no trecho 01).
- **Precisão** = acertos ÷ total de marcações do sistema.
- **Revocação** = acertos ÷ 9.
- **Gravidade**: a nota fica mais confiável se os dois bloqueios (#4 e #7) forem reconhecidos como
  bloqueio.

Comparação de tempo: não houve vistoria a pé cronometrada. Se não der para refazer, o vídeo usa só
precisão e revocação, e o tempo fica como meta do piloto.
