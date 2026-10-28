# HyperFrames: instalação e uso nesta skill

O HyperFrames (HeyGen, open source) renderiza uma composição HTML/CSS/GSAP em MP4: abre a página num Chrome headless,
avança quadro a quadro e codifica com FFmpeg. Esta skill gera a composição sozinha (`scripts/hf_project.py`):
legendas, títulos, lower thirds, números em contagem, gráficos de barra/linha, círculos de passos, cartões e pilares.
O vídeo de fundo é o vídeo já cortado (Whisper + corte de silêncio continuam no pipeline).

## Instalação (uma vez, na máquina da Layla)

```bash
# 1) Requisitos: Node.js 22+ e FFmpeg
node --version        # precisa ser v22 ou maior
ffmpeg -version

# 2) Whisper
pip install faster-whisper matplotlib pillow

# 3) HyperFrames não precisa de instalação global: o script chama `npx hyperframes@<versão> render`.
#    Na primeira execução ele baixa o Chrome headless sozinho.

# 4) (Opcional) Skills do HyperFrames para o Claude Code, úteis para pedir composições novas por conversa
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes
#    ou, avulso, dentro de um projeto de vídeo:
npx skills add heygen-com/hyperframes
npx hyperframes skills update
```

## Uso

```bash
python scripts/edit_video.py entrada.mp4 -o saida.mp4 --preset padrao            # HyperFrames (padrão)
python scripts/edit_video.py entrada.mp4 -o rascunho.mp4 --preset padrao --draft # render rápido
python scripts/edit_video.py entrada.mp4 -o saida.mp4 --preset padrao --engine ffmpeg   # sem Node/Chrome
```

A pasta `<saida>_work/hf/` é um projeto HyperFrames completo. Dá para abrir e ajustar à mão:

```bash
cd saida_work/hf
npx hyperframes preview      # prévia no navegador com live reload
npx hyperframes render       # renderiza de novo
```

## Detalhes que importam

- **GSAP local.** O script instala `gsap` via npm dentro do projeto e referencia `gsap.min.js` local. O Chrome do render
  não precisa de internet e o resultado é reprodutível. Sem npm, cai para o CDN (e avisa).
- **Fonte.** `fonts/<arquivo>` é copiado para o projeto e carregado com `@font-face` (Clarify-md no preset).
- **Versão.** O script fixa `hyperframes@0.8.209` (testada). Para outra versão: `HYPERFRAMES_VERSION=x.y.z`.
- **Chrome já instalado / ambiente sem internet.** `export HYPERFRAMES_BROWSER_PATH=/caminho/do/chrome`. Em sandbox que
  bloqueia o download do Chrome, um Chromium vem pelo npm:
  ```bash
  mkdir chr && cd chr && npm init -y && npm i @sparticuz/chromium
  node -e "import('@sparticuz/chromium').then(async m=>console.log(await m.default.executablePath()))"
  export HYPERFRAMES_BROWSER_PATH=/tmp/chromium
  ```
- **Estrutura da composição.** Cada elemento é um `.clip` com `data-start`/`data-duration`; as animações são tweens GSAP
  numa timeline pausada registrada em `window.__timelines["main"]`. Elementos de texto ficam dentro de um clip de quadro
  inteiro (o `.clip` do HyperFrames já dá caixa de quadro inteiro, então posicione o conteúdo num filho).
- **Zoom (punch_in).** Vira `tl.set("#a-roll", {scale})` em cada corte.
- **Checagem.** `npx hyperframes check` (dentro de `<saida>_work/hf`) roda lint, layout e contraste.
