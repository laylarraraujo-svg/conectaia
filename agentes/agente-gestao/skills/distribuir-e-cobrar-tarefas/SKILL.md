## Skill: Distribuir e Cobrar Tarefas

**Objetivo:** Auxiliar a Layla na distribuição de tarefas para a equipe e no acompanhamento de pendências, enviando lembretes.

**Disparo:** Solicitação da Layla para delegar uma tarefa, ou periodicamente (via n8n cron) para verificar pendências.

**Passos:**
1.  **Registrar Nova Tarefa:** Quando a Layla definir uma nova tarefa, registre-a em uma planilha de 'Tarefas da Equipe' no Google Planilhas, incluindo:
    *   Descrição da tarefa.
    *   Responsável.
    *   Prazo.
    *   Status (ex: 'Pendente', 'Em Andamento').
2.  **Distribuir Tarefa:** Envie uma notificação (via n8n, por Gmail ou WhatsApp interno) para o responsável pela tarefa, informando sobre a nova atribuição e o prazo.
3.  **Monitorar Prazos:** Periodicamente, verifique as tarefas na planilha que estão próximas do prazo ou em atraso.
4.  **Enviar Lembretes:** Para tarefas pendentes ou próximas do vencimento, envie lembretes educados para os responsáveis (via n8n, por Gmail ou WhatsApp interno). Exemplo: "Lembrete: A tarefa '[Descrição da Tarefa]' sob sua responsabilidade vence em [Data]. Favor atualizar o status."
5.  **Atualizar Status:** Quando uma tarefa for concluída, atualize seu status na planilha para 'Concluída'.
6.  **Reportar Pendências:** Inclua um resumo das principais pendências no relatório consolidado para a Layla.

**Pronto Quando:** As tarefas são distribuídas, os lembretes são enviados e o status é atualizado.