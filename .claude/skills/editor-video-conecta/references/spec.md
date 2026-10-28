# Formato do spec (`--spec edicao.json`)

Todas as chaves são opcionais. Tempos em segundos, na linha do tempo **final** (após cortar silêncios).

```json
{
  "language": "pt",
  "prompt": "Nomes e termos para ajudar o Whisper: ChatGPT, Layla, n8n",
  "font": "Montserrat",
  "theme": {"accent": "#FFD60A", "text": "#FFFFFF", "card": "#111827", "muted": "#6B7280"},
  "replacements": {"chatgpt": "ChatGPT", "n8n": "n8n"},

  "silence": {"enabled": true, "threshold_db": -32, "min_silence": 0.45, "padding": 0.10},

  "subtitles": {
    "enabled": true,
    "style": "viral",
    "position": "bottom",
    "max_words": 3,
    "uppercase": true,
    "size": 100,
    "margin_v": 400,
    "highlight_color": "#FFD60A"
  },

  "overlays": [ ... ]
}
```

## Estilos de legenda

| style | Aparência |
|-------|-----------|
| `viral` | Caixa alta, 3 palavras por vez, palavra falada em cor de destaque, contorno grosso, "pop" de entrada |
| `clean` | Frases de até 7 palavras, sem destaque por palavra, contorno fino |
| `box`   | 4 palavras, fundo escuro semitransparente, palavra ativa em destaque |
| `ref`   | Padrão da Layla: 2–3 palavras no centro, sombra suave, palavra-chave amarela na 2ª linha (ver `padrao.md`) |

`position`: `bottom` (padrão), `center`, `top`.

## Overlays

**title** — título animado (fade + subida). Use `*palavra*` para colorir com o destaque.
```json
{"type": "title", "text": "Resultados do *ano*", "start": 0.3, "duration": 2.5, "position": "top"}
```
`position`: `top`, `center`, `bottom`.

**lower_third** — nome e cargo com barra lateral, entra deslizando.
```json
{"type": "lower_third", "title": "Layla Araujo", "subtitle": "Empresa de Automações", "start": 0.5, "duration": 3.5, "y": 0.58}
```
`y` é a posição vertical como fração da altura (opcional).

**chart** — gráfico animado em cartão escuro. `kind`: `bar` ou `line`.
```json
{"type": "chart", "kind": "bar", "title": "Vendas por trimestre",
 "labels": ["T1", "T2", "T3", "T4"], "values": [120, 180, 260, 410],
 "prefix": "R$ ", "suffix": "k", "decimals": 0, "highlight": "max",
 "start": 3.0, "duration": 3.5, "position": "top"}
```
`highlight` (só barras): `"max"` (padrão), `"last"`, um índice inteiro, ou `null` para colorir todas. Números saem no formato brasileiro (1.234,5).

**stat** — número grande que conta de 0 até o valor.
```json
{"type": "stat", "value": 2450, "label": "clientes atendidos", "prefix": "+", "start": 6.0, "duration": 2.5, "position": "top"}
```

`position` para chart/stat: `top`, `center`, `bottom`, `top-left`, `top-right`, `bottom-left`, `bottom-right`.

## Outros campos

`preset` (nome em `presets/`), `punch_in` (`enabled`, `levels`, `max_hold`, `min_hold`) e os overlays `numbered_title`, `steps`, `cards`, `pillars` estão em `padrao.md`.

## Dicas de composição

- Em vídeo vertical, deixe gráficos em `top` ou `center` e legenda em `bottom` para não sobrepor.
- Gráfico leva ~1,3 s para animar; use `duration` ≥ 3 para o espectador ler o valor final.
- Evite dois overlays ocupando a mesma região ao mesmo tempo.
