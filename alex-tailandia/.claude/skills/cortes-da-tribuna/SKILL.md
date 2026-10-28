---
name: cortes-da-tribuna
description: Transforma a gravação de uma sessão da Câmara de Mogi Guaçu em 3 a 5 cortes verticais da fala do vereador Alex Tailândia, com legenda e título. Use quando mandarem o vídeo/link da sessão, ou pedirem "corta a tribuna", "cortes da sessão".
---

# Cortes da tribuna

1. **Obter o vídeo:** arquivo enviado pelo gabinete, ou link da transmissão oficial da Câmara. Confirme o direito de uso da gravação (ver `regras-e-limites.md` → Recursos públicos).
2. **Localizar a fala do Alex:** transcreva (a skill `video-editor` usa Whisper com tempo por palavra) e marque início e fim de cada fala dele.
3. **Escolher 3–5 trechos de 30–60 s.** Critérios, em ordem:
   - frase de impacto que se entende **sem contexto**;
   - número/fato concreto (valor, nº do projeto);
   - pilar com menos posts na semana;
   - reação do plenário (aparte, votação).
   Para cada trecho, entregue: minuto inicial/final, frase-gancho, título de tela (≤ 8 palavras), pilar.
4. **Checar regras:** o trecho cortado não pode distorcer o sentido da fala, nem a de outro vereador. Se cortar aparte de adversário, mantenha contexto suficiente.
5. **Editar** com a skill `video-editor`: vertical 9:16, enquadramento no Alex, legenda palavra a palavra, título no topo, sem silêncios. Use `dossie/estilo-de-edicao.md` se existir.
6. Salve em `pautas/AAAA-MM-DD-sessao/` com `status.md` (formato Tribuna) e `legendas.md`, e mande para aprovação.
