## Skill: Consolidar Relatórios Operacionais

**Objetivo:** Reunir os relatórios gerados por todos os agentes operacionais (Vendas, Atendimento, Marketing, Financeiro) em um único resumo para a Layla.

**Disparo:** Diariamente, semanalmente ou mensalmente (via n8n cron), conforme a cadência de relatório geral desejada pela Layla.

**Passos:**
1.  **Coletar Relatórios Individuais:** Solicite (via n8n) os relatórios mais recentes de cada Agente (Vendas, Atendimento, Marketing, Financeiro).
2.  **Extrair Pontos Chave:** Leia e extraia os principais resultados, métricas de sucesso, alertas e observações de cada relatório individual.
3.  **Criar Resumo Executivo:** Compile os pontos chave em um resumo executivo claro e conciso no Google Docs. Organize por área e destaque os resultados mais importantes e quaisquer pendências ou escalonamentos.
4.  **Verificar Prioridades:** Assegure-se de que a prioridade de Vendas seja refletida na apresentação, caso haja algum conflito de informações ou resultados.
5.  **Enviar para Layla:** Apresente o resumo consolidado para a Layla via Gmail ou o canal de comunicação preferencial (via n8n), conforme sua preferência por 'Resumo no chat'.
6.  **Registro no Supabase:** Salve o relatório consolidado no Supabase.

**Pronto Quando:** Os relatórios individuais são consolidados em um resumo executivo e entregues à Layla.