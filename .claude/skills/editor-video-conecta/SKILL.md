---
name: editor-video-conecta
description: Editor de vídeo automático do Colégio Conecta Araras (estilo do Reel de referência da Layla) — transcreve a fala (Whisper local), corta silêncios, gera legendas animadas estilo Reels/TikTok/Shorts, e adiciona títulos, lower thirds e gráficos animados (barras, linha, pilares, números em contagem) renderizados com HyperFrames (HTML+GSAP) e FFmpeg. Use SEMPRE que o usuário pedir para editar um vídeo, legendar, "colocar legenda", cortar pausas/silêncios/"tirar os vazios", deixar o vídeo dinâmico, adicionar gráficos ou textos animados, ou montar um editor/pipeline de vídeo, mesmo que não diga "editor". Também vale para edit video, add captions, remove silence, auto-subtitles, jump cuts, animated charts overlay.
---

# Editor de vídeo (legendas, cortes de silêncio, gráficos)

Esta skill edita vídeos de fala (talking head, aulas, depoimentos, Reels) rodando tudo localmente: Whisper para transcrever, FFmpeg para cortar silêncio e **HyperFrames** (composição HTML/CSS/GSAP renderizada em Chrome headless) para legendas, títulos e gráficos animados. Há um motor alternativo só com FFmpeg (`--engine ffmpeg`: ASS + matplotlib) para máquinas sem Node/Chrome.

## Padrão de edição da Layla (use por padrão)

Quando a Layla pedir uma edição sem especificar o estilo, aplique o preset `padrao` (`--preset padrao`), copiado do Reel de referência (https://www.instagram.com/reel/Ddewmw8PGtf/): fonte Cal Sans, legenda central de 2–3 palavras com palavra-chave amarela (#F9D41A) 40% maior na 2ª linha, títulos numerados, círculos de passos, cartões, caixa de vidro com texto brilhante (`glass_badge`), número gigante (`big_number`), gráfico de pilares, inserts de b-roll (`broll`), cartão "Seguir" no final (`follow_cta`) e zoom alternado a cada corte. Medidas e incertezas em `references/padrao.md`. Se ela pedir outro estilo, ele vence.

**Sugira os elementos lendo a transcrição:** dinheiro/preço → `glass_badge` ou `big_number`; lista ("três coisas", "primeiro") → `steps` + `numbered_title`; enumeração de dores/itens → `cards`; comparação de números → `pillars`; último 3–4 s → `follow_cta` com `@colegioconectaararas` (confirme o @ com a Layla). Mostre o plano (tempo + elemento) antes do render final.

## Instalação neste ambiente (cada sessão nova)

```bash
bash .claude/skills/editor-video-conecta/setup.sh
```

## Dependências

- Node.js 22+ e FFmpeg (`ffmpeg`, `ffprobe`). Para `--engine ffmpeg` o FFmpeg precisa de libass (`ffmpeg -filters | grep -E " ass | silencedetect "`).
- Python 3.9+: `pip install faster-whisper matplotlib pillow`.
- HyperFrames: sem instalação global; o script chama `npx hyperframes@0.8.209 render` e o Chrome headless é baixado na primeira vez. Instalação das skills do HyperFrames e solução para ambientes sem internet: `references/hyperframes.md`.
- O Whisper baixa o modelo na primeira execução (~460 MB no `small`). Se a rede bloquear, ver "Sem acesso ao Whisper".

## Fluxo recomendado

1. **Entenda o pedido.** Formato do vídeo (vertical 9:16 ou horizontal), estilo de legenda, onde entram gráficos/títulos. Se o usuário não disse, use os padrões: legenda `viral`, corte de silêncio ligado, sem overlays.
2. **Transcreva primeiro e mostre o texto** (`scripts/transcribe.py`). Whisper erra nomes próprios e termos técnicos; mostre as palavras duvidosas e corrija editando `transcript.json` ou usando `replacements` no spec. Legenda errada é o defeito mais visível no resultado final.
3. **Monte o spec** (`references/spec.md` tem todos os campos). Tempos de overlays são na linha do tempo **final**, depois dos cortes — por isso renderize o rascunho, veja em que momento cada fala cai e só então posicione gráficos.
4. **Rascunho rápido:** `--draft` (540p). Extraia 3–4 frames com `ffmpeg -ss T -i out.mp4 -frames:v 1` e olhe antes de gastar tempo no render final.
5. **Render final** sem `--draft` e entregue o arquivo ao usuário com uma linha dizendo quanto silêncio foi removido.

## Comando principal

```bash
python scripts/edit_video.py entrada.mp4 -o saida.mp4 --spec edicao.json
python scripts/edit_video.py entrada.mp4 -o saida.mp4 --silence --subtitles viral   # sem spec
python scripts/edit_video.py entrada.mp4 -o rascunho.mp4 --spec edicao.json --draft
```

Adicione `--preset padrao` para usar o padrão da Layla. `--engine hyperframes` é o padrão; `--engine ffmpeg` usa o motor sem Chrome. O pipeline faz: transcrição (cacheada em `<saida>_work/transcript.json`) → corte de silêncio → legendas/títulos → gráficos → render. Use `--transcript arquivo.json` para reaproveitar um transcript já corrigido.

Scripts individuais, quando só uma etapa for necessária:
- `scripts/transcribe.py` — transcript com tempo por palavra.
- `scripts/cut_silence.py` — só corta silêncio (`--threshold`, `--min-silence`, `--padding`).
- `scripts/hf_project.py` — monta e renderiza o projeto HyperFrames (overlays) a partir de vídeo + transcript + spec.
- `scripts/build_ass.py` — gera só o `.ass` de legendas (motor ffmpeg).
- `scripts/charts.py` — pré-visualiza um gráfico isolado.

## Decisões de design (e o porquê)

- **Transcrever antes de cortar.** O Whisper acerta mais com pausas naturais; depois os tempos das palavras são remapeados para o vídeo cortado, então a legenda nunca dessincroniza.
- **Padding de 0.10 s nas bordas da fala.** Cortar rente corta consoantes e soa robótico. Para um ritmo mais agressivo (jump cuts), reduza `min_silence` para 0.3 s e `padding` para 0.06.
- **Threshold de silêncio:** -32 dB serve para áudio limpo. Com ruído de fundo, suba para -26 dB; se estiver cortando respiração/fala baixa, desça para -38 dB. Ajuste olhando `Corte de silêncio: {...}` na saída.
- **Legenda `viral` em vertical** fica a ~22% da base para não cair sob a interface do Reels/TikTok. Em horizontal fica rente à base.
- **Gráficos com dados do usuário.** Nunca invente números para um gráfico; se o dado não está no vídeo nem foi fornecido, pergunte.
- **Fonte:** o padrão usa Clarify-md. Arquivos `.ttf/.otf` colocados em `fonts/` são achados pelo nome e levados ao render; sem o arquivo, o script avisa e cai para Montserrat/Poppins/Inter/Arial. Para outra fonte, passe `"font"` no spec.

## Sem acesso ao Whisper

Se o download do modelo falhar (rede restrita), não trave: peça ao usuário para rodar `transcribe.py` na máquina dele, ou aceite um `transcript.json` no formato abaixo e use `--transcript`.

```json
{"words": [{"start": 0.31, "end": 0.62, "word": "Olá"}]}
```

## Problemas comuns

- *`Chrome not found` no render:* o HyperFrames não conseguiu baixar o Chrome. Aponte um Chrome existente com `HYPERFRAMES_BROWSER_PATH` (ver `references/hyperframes.md`) ou use `--engine ffmpeg`.
- *Render HyperFrames bloqueado por `sub_timeline_script_failure`:* o GSAP não carregou. O script já usa `gsap.min.js` local; confira se `npm install` funcionou na pasta `<saida>_work/hf`.
- *Legenda não aparece:* o filtro `ass` precisa de libass; confirme com o comando em Dependências.
- *Fonte estranha na legenda:* a família pedida não está instalada; use `fc-list : family` para ver as disponíveis.
- *Render lento:* use `--draft` para iterar e só no final render completo; vídeos longos com legenda levam cerca de 1x a duração em CPU comum.
- *Gráfico some cedo:* `duration` do overlay vale para a linha do tempo final (após cortes), não a original.
