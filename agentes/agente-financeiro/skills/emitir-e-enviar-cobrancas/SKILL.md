## Skill: Emitir e Enviar Cobranças para Inadimplentes

**Objetivo:** Identificar pais inadimplentes e preparar mensagens de cobrança para revisão e envio pelo Kelvin.

**Disparo:** Diariamente ou semanalmente (via n8n cron) para verificar a planilha de pagamentos.

**Passos:**
1.  **Identificar Inadimplentes:** Acesse a planilha de 'Pagamentos' no Google Planilhas. Compare os pagamentos esperados com os recebidos para identificar contas em atraso.
2.  **Verificar Histórico:** Consulte o Supabase para verificar o histórico de cobranças anteriores para o cliente. Evite duplicidade ou envio de mensagens inadequadas.
3.  **Gerar Mensagem de Cobrança:** Elabore uma mensagem de cobrança educada e profissional, seguindo a voz da marca. A mensagem deve informar o valor em atraso, a data de vencimento original e as opções para regularização (sem mencionar valores específicos, mas direcionando para contato humano). Exemplo: "Prezado(a) [Nome do Pai], identificamos um débito referente à mensalidade de [Mês/Ano]. Gostaríamos de conversar sobre a regularização. Por favor, entre em contato com nosso setor financeiro para mais detalhes."
4.  **Preparar para Revisão:** Envie a mensagem de cobrança gerada para o Kelvin via Gmail (como rascunho ou para um grupo interno), para que ele possa revisar e realizar o contato final com o cliente.
5.  **Atualizar Status:** Marque o status do cliente como 'Aguardando Cobrança' ou 'Cobrança Enviada (para revisão)' na planilha do Google Planilhas e no Supabase.

**Pronto Quando:** A mensagem de cobrança é gerada, enviada para revisão do Kelvin e o status é atualizado.