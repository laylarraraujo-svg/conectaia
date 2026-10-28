---
name: gerar-carrossel
description: Gera os slides do carrossel do vereador Alex Tailândia a partir de pautas/*/carrossel.md, nos estilos fixos (Documento, Explicando, Como votei, Antes/depois, Frase da tribuna). Use depois de criar-conteudo ou quando pedirem "faz o carrossel".
---

# Gerar carrossel

1. Leia `carrossel.md` da pauta, `dossie/formatos.md` (estilos) e `dossie/identidade-visual.md`. Se a identidade visual não existir, pergunte cores, fonte e foto padrão antes de começar e salve a resposta nesse arquivo.
2. Use a skill **`carrossel-instagram`** passando:
   - tamanho 1080×1350 (4:5), 6–8 slides;
   - cores, fonte e foto do Alex de `identidade-visual.md`;
   - o estilo escolhido, com estas regras:
     - **Documento:** print real do documento (fornecido pelo gabinete), trecho em destaque com marca-texto, nº e data visíveis. Nunca recriar ou "simular" documento.
     - **Explicando:** 1 ideia por slide, título grande, ícone simples.
     - **Como votei:** projeto | voto do Alex | resultado | 1 linha de porquê.
     - **Antes/depois:** fotos reais com data. Nunca gerar foto por IA de local real.
     - **Frase da tribuna:** citação literal (conferir na transcrição) + foto real da sessão.
   - último slide: CTA + @alex.tailandia.
3. **Proibido:** gerar por IA rosto, foto ou cena de pessoa ou lugar real. Fotos vêm do gabinete; IA só para fundos, ícones e tipografia.
4. Exporte os PNGs em `pautas/<pauta>/carrossel/slide-01.png …` e atualize `status.md`.
