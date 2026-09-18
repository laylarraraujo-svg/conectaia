## Skill: Agendar Encontro com Especialista

**Objetivo:** Marcar um horário para o lead encontrar um especialista do Colégio Conecta Araras, utilizando o Google Agenda.

**Disparo:** O lead expressa interesse em agendar um encontro após a qualificação inicial (invocado pela skill `recepcionar-e-qualificar-lead` ou diretamente).

**Passos:**
1.  **Verificar Disponibilidade:** Acesse o Google Agenda para consultar os horários disponíveis dos especialistas para encontros. Priorize horários que estejam alinhados com a conveniência do lead, se ele expressou alguma preferência.
2.  **Propor Horários:** Apresente 2-3 opções de data e horário ao lead via WhatsApp. Exemplo: "Temos disponibilidade nos seguintes horários: [Dia da Semana, Dia/Mês, Horário] ou [Dia da Semana, Dia/Mês, Horário]. Qual seria o melhor para você?"
3.  **Confirmar Escolha:** Aguarde a escolha do lead. Em caso de indecisão, ofereça mais opções ou pergunte sobre a preferência de dia/período.
4.  **Criar Evento no Google Agenda:** Uma vez confirmado o horário, crie um evento no Google Agenda com os seguintes detalhes:
    *   **Título:** 'Encontro Especialista - [Nome do Lead] - [Nome do Aluno]'
    *   **Participantes:** E-mail do especialista e, se disponível, e-mail do lead.
    *   **Descrição:** Inclua as informações coletadas do lead (nome do aluno, turma de interesse, escola atual) e um breve lembrete sobre o propósito do encontro (apresentação da proposta, discussão de valores).
    *   **Local:** Endereço do Colégio Conecta Araras.
5.  **Enviar Confirmação ao Lead:** Envie uma mensagem de confirmação ao lead via WhatsApp, com os detalhes do agendamento. Exemplo: "Perfeito, [Nome do Lead]! Seu encontro com nosso especialista está confirmado para [Dia da Semana, Dia/Mês] às [Horário] em nosso colégio. Estamos ansiosos para recebê-lo(a)! Um lembrete será enviado próximo à data."
6.  **Atualizar Status no Google Planilhas:** Altere o status do lead no Google Planilhas para 'Agendado'.
7.  **Registro no Supabase:** Salve a confirmação do agendamento e o ID do evento do Google Agenda no histórico de conversas do lead no Supabase.

**Pronto Quando:** O evento é criado no Google Agenda e a confirmação é enviada ao lead.