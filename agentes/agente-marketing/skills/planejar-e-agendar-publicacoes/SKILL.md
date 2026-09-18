## Skill: Planejar e Agendar Publicações

**Objetivo:** Agendar posts em redes sociais (Instagram) e campanhas de anúncios (Meta Ads) após a aprovação do conteúdo humano.

**Disparo:** Conteúdo aprovado pela Laura (Marketing) ou Layla.

**Passos:**
1.  **Receber Conteúdo Aprovado:** Confirme que o conteúdo (copy, imagens/vídeos) foi aprovado e está finalizado no Google Drive.
2.  **Definir Plataforma e Data/Hora:** Com base na estratégia, determine onde (Instagram, Meta Ads) e quando (data e hora) o conteúdo deve ser publicado.
3.  **Configurar Agendamento via n8n:**
    *   **Para Instagram:** Utilize um nó do n8n para interagir com a API do Instagram (via Evolution API ou Uazapi, se houver integração, ou através de um conector de redes sociais do n8n) para agendar o post. Inclua copy, imagem/vídeo e hashtags.
    *   **Para Meta Ads:** Configure um fluxo no n8n para criar ou atualizar uma campanha no Meta Ads, injetando o criativo (copy e imagem/vídeo) e definindo o orçamento e público-alvo, conforme as instruções da Laura.
4.  **Confirmar Agendamento:** Verifique se o agendamento foi configurado corretamente na plataforma ou no n8n.
5.  **Atualizar Status:** Marque o status do conteúdo como 'Agendado' ou 'Publicado' no Supabase.

**Pronto Quando:** O conteúdo é agendado com sucesso na(s) plataforma(s) e o status é atualizado.