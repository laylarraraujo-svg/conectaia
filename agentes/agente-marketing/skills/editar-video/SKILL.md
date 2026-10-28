## Skill: Editar Vídeo (vídeo final + capa + legenda)

**Objetivo:** Receber um vídeo bruto e entregar, no modelo escolhido, o vídeo 100% editado (cortes, legendas, títulos, gráficos, fotos/vídeos, trilha, cartão final), a capa e a legenda do post, prontos para aprovação.

**Disparo:** A Layla ou a Laura envia um vídeo e pede para editar ("edita esse vídeo", "faz o Reels disso", "coloca legenda e música").

**Ferramenta:** `editor-de-video/editar.py` (guia completo em `editor-de-video/LEIA-ME.md`). Rode sempre de dentro de `editor-de-video/`.

**Passos:**

1. **Receber os arquivos.** Vídeo enviado no chat, link do Google Drive (baixe com o conector do Drive) ou arquivo em `editor-de-video/entrada/`. Fotos/vídeos extras vão para `entrada/<nome-do-video>-midias/`. Se as fotos tiverem nomes genéricos (IMG_1234.jpg), olhe cada uma e renomeie pelo assunto (`biblioteca.jpg`, `robotica.jpg`): é assim que o sistema sabe em que momento inserir.
2. **Escolher o modelo.** Se a pessoa não disse, pergunte mostrando as opções de `python editar.py --listar-modelos` (`conecta-reels` é o padrão). Pergunte também se há música; sem música o vídeo sai só com a voz. Nunca use música com direitos autorais que a escola não tenha licença para usar.
3. **Preparar:** `python editar.py <video> --modelo <id> --preparar`. Leia `saida/<video>/transcricao.txt`.
4. **Conferir a transcrição.** Mostre o texto e aponte palavras duvidosas (nomes próprios, "Conecta", termos pedagógicos). Corrija com `substituicoes` no plano. Legenda errada é o defeito mais visível.
5. **Montar o plano** em `entrada/<video>.plano.json` (formato no LEIA-ME):
   - `gancho`: título de abertura curto e forte (use a skill `gancho-dos-3-segundos` ou `hooks-magneticos`), com `*palavra*` em destaque.
   - `overlays`: números e gráficos **somente com dados ditos no vídeo ou fornecidos pela equipe**. Nunca invente números. Posicione pelos tempos da `transcricao.txt`.
   - `broll`: só se precisar de posição exata; senão deixe o sistema inserir pelo nome do arquivo.
   - `pessoa`: nome e papel, no modelo `depoimento`.
   - `capa.titulo`: até 6 palavras, uma em destaque.
   - `legenda`: escreva o texto final do post na voz da marca (Premium e Motivador, sem gírias; ver `contexto/voz-da-marca.md`): gancho na 1ª linha, 2 a 4 frases de valor, chamada para ação, hashtags do modelo. Respeite `contexto/regras-da-casa.md`: nunca prometer resultados, nunca citar valores ou descontos.
6. **Rascunho:** rode com `--midias`, `--musica`, `--plano` e `--rascunho`. Extraia 4 a 6 quadros (`ffmpeg -ss T -i saida/<video>/video-rascunho.mp4 -frames:v 1 q.jpg`) e olhe: legenda legível, nada sobreposto, fotos no momento certo, cartão final correto. Olhe também a `capa.jpg`. Ajuste o plano e repita se precisar.
7. **Final:** mesmo comando sem `--rascunho`.
8. **Entregar** o `video-final.mp4`, a `capa.jpg` e o texto de `legenda.txt` no chat (e salve no Google Drive, na pasta de conteúdos, se o conector estiver disponível). Diga em uma linha quanto silêncio foi removido e onde entrou cada foto (`resumo.json`).
9. **Aprovação:** não publique nem agende. Avise que está pronto para a aprovação da Laura ou da Layla.

**Pronto quando:** vídeo final, capa e legenda foram entregues, conferidos em quadros e aguardam aprovação.

**Aprendizados:** quando a Layla ou a Laura corrigir algo de estilo (cor, tamanho, ritmo, tom da legenda), ajuste o modelo em `editor-de-video/modelos/` e registre no `memory.md`.
