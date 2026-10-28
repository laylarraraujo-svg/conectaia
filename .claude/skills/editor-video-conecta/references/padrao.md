# Padrão de edição (baseado no Reel de referência)

Medido a partir do Reel de referência (talking head vertical 1080x1920, 66,9 s) por análise de quadros e pixels.
A resolução dos quadros que consegui ver era baixa, então valores de fonte são aproximados (ver "Incertezas").

## O que o padrão copia

| Elemento | Como é no Reel | Como o preset reproduz |
|----------|----------------|------------------------|
| Cor de destaque | Amarelo ≈ `#F9D41A` (média dos pixels amarelos em vários quadros) | `theme.accent` |
| Texto | Branco com sombra suave, sem contorno grosso | `style: "ref"` (sombra, contorno 0) |
| Fonte | **Cal Sans** (escolhida pela Layla; o Reel usa uma sans geométrica tipo Poppins Bold) | `font: "Cal Sans"` — arquivo em `fonts/CalSans-Regular.ttf` |
| Legenda | 2–3 palavras por vez, centro do quadro (~53% da altura), corpo ≈ 72 px em 1920 (3,75% da altura), linhas coladas | `pos_y: 0.53`, `max_words: 3`, `size_ratio: 0.0375`, `line_height: 1.0` |
| Palavra-chave | Última(s) palavra(s) vão para 2ª linha, maiores (×1,4, medido: altura de maiúscula 71 px), amarelas, caixa alta | `highlight_words`, números/moedas, `*palavra*`, `auto_long` |
| Título de lista | Numeral amarelo grande + título branco em caixa alta, com "pop" | overlay `numbered_title` (a legenda pausa enquanto ele aparece) |
| Contador de passos | Círculos 1-2-3 no topo, o ativo com anel tracejado amarelo | overlay `steps` |
| Ícones | Cartões quadrados com borda tracejada amarela surgindo em sequência | overlay `cards` (texto ou imagem PNG) |
| Gráfico de ranking | Fundo escuro em degradê, pilares 3D coloridos, título amarelo + subtítulo branco | overlay `pillars` (tela cheia; `colors` por barra, `logos` opcionais) |
| Caixa de vidro | "$$$" amarelo com brilho dentro de caixa escura translúcida no topo (≈67% da largura, 10–25% da altura); o texto entra rolando de baixo com desfoque | overlay `glass_badge` |
| Número gigante | "$10,000" amarelo com brilho no topo, sem caixa | overlay `big_number` (conta até o valor) |
| B-roll | Trechos de filme em tela cheia, legenda continua por cima | overlay `broll` (clipe fornecido pela Layla) |
| CTA final | Cartão branco arredondado (≈66% da largura, centro a 64% da altura): foto com anel degradê, @ em negrito, botão "Follow" que um cursor clica e vira "Following" roxo/laranja | overlay `follow_cta` |
| Ritmo | Mudança visual a cada ~3–4 s (zoom/plano), rajada de cortes de ~0,25–0,5 s em trechos de ênfase | `punch_in` alterna 100% / 114% / 100% / 126% a cada corte e no máx. a cada 3,5 s |

## Uso

O padrão é renderizado com HyperFrames (HTML/GSAP). `--engine ffmpeg` produz o mesmo estilo com ASS/matplotlib, com acabamento mais simples.

```bash
python scripts/edit_video.py entrada.mp4 -o saida.mp4 --preset padrao
python scripts/edit_video.py entrada.mp4 -o saida.mp4 --preset padrao --spec extras.json   # extras sobrepõem o preset
```

O preset fica em `presets/padrao.json`. O `spec` do usuário é mesclado por cima (só as chaves informadas mudam).

## Overlays novos

```json
{"type": "numbered_title", "number": 1, "text": "Solutions", "start": 4.0, "duration": 2.0}
{"type": "steps", "count": 3, "active": 1, "start": 3.8, "duration": 2.5, "position": "top"}
{"type": "cards", "items": [{"text": "DÍVIDA"}, {"image": "peso.png"}], "start": 10, "duration": 3, "position": "top"}
{"type": "pillars", "title": "The Richest Companies", "subtitle": "on the planet",
 "labels": ["Meta", "Apple"], "values": [3, 4], "colors": ["#1D6FEA", "#D9D9DE"],
 "logos": ["meta.png", "apple.png"], "prefix": "$", "suffix": "T", "decimals": 1,
 "start": 20, "duration": 3, "position": "full"}
```

```json
{"type": "glass_badge", "text": "$$$", "start": 0.3, "duration": 2.2}
{"type": "big_number", "value": 10000, "prefix": "R$ ", "start": 30, "duration": 2}
{"type": "big_number", "text": "R$ 10 mil", "start": 30, "duration": 2}
{"type": "broll", "src": "cena.mp4", "from": 4.0, "start": 18, "duration": 1.5}
{"type": "follow_cta", "handle": "@colegioconectaararas", "avatar": "logo.png", "start": 62, "duration": 4, "click_at": 1.6,
 "button": "Seguir", "button_done": "Seguindo"}
```

Esses quatro só existem no motor HyperFrames (padrão). `broll`: `from` é o segundo do clipe onde começar; o áudio do clipe fica mudo (use `volume` > 0 para ouvir).

## Incertezas (diga ao usuário se importarem)

- A fonte é a Cal Sans por decisão da Layla (só tem um peso). O Reel usa uma sans em negrito parecida com Poppins Bold.
- Medidas refeitas no vídeo original em 1080x1920 (out/2026). O cartão do CTA usa Montserrat/Arial, como a interface do Instagram.
- Os ícones 3D dos cartões e os logos do gráfico do Reel são imagens externas; o preset só cria o cartão e aceita as imagens do usuário em `image`/`logos`.
- Cenas de b-roll (trechos de filmes) e rajadas de cortes rápidos não são automatizadas: o usuário fornece os clipes.
- Os quadros foram vistos em baixa resolução; ajuste fino de tamanho/posição pode ser necessário com o vídeo real.
