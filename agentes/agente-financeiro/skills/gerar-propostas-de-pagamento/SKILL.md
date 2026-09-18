## Skill: Gerar Propostas de Pagamento

**Objetivo:** Criar rascunhos de propostas de pagamento ou renegociação para clientes inadimplentes, para serem finalizadas e enviadas pelo Kelvin.

**Disparo:** Solicitação do Kelvin (Financeiro) para um cliente específico ou identificação de um inadimplente que necessita de uma proposta de renegociação.

**Passos:**
1.  **Coletar Dados do Cliente:** Acesse o Supabase e o Google Planilhas para obter o histórico de pagamentos do cliente, valor total em atraso e outras informações relevantes.
2.  **Analisar Cenário:** Com base em regras predefinidas (se houver no contexto, ou solicitando ao Kelvin), determine possíveis cenários de parcelamento ou condições de renegociação (ex: número máximo de parcelas, juros aplicáveis).
3.  **Estruturar Proposta:** Elabore um rascunho de proposta de pagamento. A proposta deve ser clara e incluir:
    *   Valor total do débito.
    *   Sugestão de parcelamento (ex: 3x, 6x).
    *   Valores das parcelas (sempre indicando que são 'sugestões' e precisam de validação humana).
    *   Condições gerais (ex: 'sujeito à aprovação').
4.  **Preparar para Revisão:** Envie o rascunho da proposta para o Kelvin via Gmail (como rascunho ou para um grupo interno), para que ele possa revisar, ajustar e apresentar ao cliente.
5.  **Registro no Supabase:** Salve a proposta gerada no histórico do cliente no Supabase.

**Pronto Quando:** O rascunho da proposta de pagamento é gerado, enviado para revisão do Kelvin e registrado.