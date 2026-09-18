## Skill: Atualizar CRM e Pipeline

**Objetivo:** Manter o status dos leads e o pipeline de vendas atualizados na planilha do Google Planilhas.

**Disparo:** Após cada interação significativa com um lead (qualificação, agendamento, follow-up, mudança de status) ou a cada X horas (via n8n cron).

**Passos:**
1.  **Identificar Lead:** Use o número de WhatsApp ou nome do lead para localizá-lo na planilha de CRM no Google Planilhas.
2.  **Determinar Status Atualizado:** Com base na última interação ou no resultado de uma skill anterior, defina o novo status do lead:
    *   'Novo Lead'
    *   'Qualificado'
    *   'Agendado'
    *   'Reunião Realizada'
    *   'Proposta Enviada'
    *   'Matrícula Finalizada' (adiantado para humano)
    *   'Lead Frio' (se não houver resposta após follow-ups)
    *   'Descartado'
3.  **Atualizar Planilha:** Modifique a linha correspondente ao lead no Google Planilhas, atualizando a coluna de 'Status' e, se aplicável, outras informações como data da última interação, próxima ação, etc.
4.  **Registrar Ação:** Salve a atualização do status no histórico de conversas do lead no Supabase.

**Pronto Quando:** O status do lead é atualizado corretamente na planilha do Google Planilhas.