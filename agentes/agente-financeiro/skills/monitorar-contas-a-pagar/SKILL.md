## Skill: Monitorar Contas a Pagar e Enviar Lembretes

**Objetivo:** Acompanhar as despesas e contas a pagar da escola e enviar lembretes para o Kelvin sobre vencimentos próximos ou gastos excessivos.

**Disparo:** Diariamente ou semanalmente (via n8n cron) para verificar a planilha de despesas.

**Passos:**
1.  **Acessar Planilha de Despesas:** Consulte a planilha de 'Despesas e Contas a Pagar' no Google Planilhas.
2.  **Identificar Vencimentos Próximos:** Verifique as contas com vencimento nos próximos 3-5 dias.
3.  **Verificar Gastos:** Compare os gastos atuais com orçamentos predefinidos (se houver). Identifique se algum item está com gasto 'muito alto' ou 'acima do esperado'.
4.  **Gerar Lembretes/Alertas:**
    *   **Lembrete de Vencimento:** Para contas próximas ao vencimento, crie uma mensagem: "Lembrete: A conta [Nome da Conta] no valor de [Valor] vence em [Data]."
    *   **Alerta de Gasto:** Se identificar gasto excessivo: "Alerta: O gasto com [Categoria] está acima do esperado neste mês. Favor verificar."
5.  **Enviar para Kelvin:** Envie os lembretes e alertas para o Kelvin via Gmail (ou outro canal de comunicação interno via n8n).
6.  **Atualizar Status:** Marque o status da conta como 'Lembrete Enviado' na planilha do Google Planilhas.

**Pronto Quando:** Lembretes e alertas são gerados e enviados para o Kelvin.