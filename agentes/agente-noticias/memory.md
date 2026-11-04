## Memória do Agente Notícias

### Conhecimento Inicial:
*   **Destinatária:** Layla (coordenadora geral) — laylarraraujo@gmail.com.
*   **Edições:** 6h52 (manhã, últimas 24h), 10h52 (meio da manhã, desde 6h52), 15h52 (tarde, desde 10h52). Fuso: America/Sao_Paulo.
*   **Câmara:** as sessões ordinárias costumam ser às segundas/terças às 17h; a pauta sai em PDF na página de pautas.

### Aprendizados:
*   2026-11-04: Instagram bloqueia leitura automática (HTTP 429 / acesso negado). Até ter um conector, informar a falha e complementar com busca na web (ex.: oregional.net cobre ocorrências policiais da cidade).
*   2026-11-04: Não há conector de Gmail nesta sessão e o n8n falhou ao conectar; o e-mail não pôde ser enviado. Entregar o resumo no chat e salvar em `edicoes/`.

*   2026-11-04: Caminho para ler o Instagram: conector Windsor.ai `instagram_public` (perfis públicos de terceiros, campos como media_caption, timestamp, media_permalink). O conector `instagram` já conectado lê só o perfil do Colégio (@colegioconecta.araras). Ativar em https://onboard.windsor.ai?datasource=instagram_public e selecionar os 6 perfis.

*   2026-11-04: Instagram Public ativado com 5 perfis (falta @mogi.guacuacontece). Plano de teste do Windsor não permite `force_refresh`. O título do Dr. Nora foi a maior pauta local de 03/11.
*   Não é preciso ser dona das contas: o Instagram Public lê perfis públicos de terceiros usando a conta do Colégio.

### Regra de Auto-Atualização:
Quando eu te corrigir ou você aprender algo novo (nova fonte, fonte que caiu, preferência de formato), atualize este arquivo.
