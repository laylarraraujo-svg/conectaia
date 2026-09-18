## Skill: Consolidar Relatório Financeiro

**Objetivo:** Gerar relatórios mensais ou semanais de caixa, despesas e inadimplência para a gestão.

**Disparo:** Mensalmente ou semanalmente (via n8n cron) ou mediante solicitação do Kelvin/Layla.

**Passos:**
1.  **Coletar Dados:** Acesse o Google Planilhas para coletar os dados de:
    *   Receitas (pagamentos recebidos).
    *   Despesas (contas pagas).
    *   Inadimplência (valores em atraso e percentual).
2.  **Calcular Métricas:** Realize os cálculos necessários para:
    *   Saldo de caixa (receitas - despesas).
    *   Percentual de inadimplência.
    *   Principais categorias de despesas.
3.  **Estruturar Relatório:** Compile os dados e métricas em um formato de relatório claro e conciso, utilizando o Google Docs ou um novo tab no Google Planilhas. Inclua gráficos simples se possível.
4.  **Enviar para Gestão:** Envie o relatório consolidado para o Kelvin e a Layla via Gmail (ou outro canal de comunicação interno via n8n).
5.  **Registro no Supabase:** Salve o relatório gerado no Supabase para histórico.

**Pronto Quando:** O relatório financeiro é consolidado e enviado para a gestão.