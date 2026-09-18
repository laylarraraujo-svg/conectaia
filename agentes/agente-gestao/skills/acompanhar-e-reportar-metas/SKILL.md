## Skill: Acompanhar e Reportar Metas

**Objetivo:** Monitorar o progresso das metas operacionais e estratégicas do Colégio Conecta Araras e reportar o status para a Layla.

**Disparo:** Diariamente ou semanalmente (via n8n cron) ou mediante solicitação da Layla.

**Passos:**
1.  **Acessar Metas:** Consulte a planilha de 'Metas e Indicadores' no Google Planilhas, onde as metas de cada área estão definidas.
2.  **Coletar Dados de Desempenho:** Integre com os outros agentes (Vendas, Atendimento, Marketing, Financeiro) via n8n para coletar as métricas de sucesso de cada um (agendamentos, tempo de atendimento, conversão, inadimplência).
3.  **Comparar e Analisar:** Compare o desempenho atual com as metas estabelecidas. Identifique se as metas estão sendo atingidas, se há desvios significativos ou se alguma área precisa de atenção.
4.  **Gerar Relatório de Metas:** Compile um relatório conciso no Google Docs ou em uma aba específica do Google Planilhas, destacando o status de cada meta, o progresso e quaisquer observações relevantes. Exemplo: 'Meta de Agendamentos (Vendas): 80% atingida. Meta de Inadimplência (Financeiro): Dentro do esperado.'
5.  **Enviar para Layla:** Apresente o relatório de metas para a Layla via Gmail ou o canal de comunicação preferencial (via n8n).
6.  **Registro no Supabase:** Salve o relatório de metas no Supabase para histórico e acompanhamento.

**Pronto Quando:** O progresso das metas é acompanhado, o relatório é gerado e enviado para a Layla.