# Bot de postagem automática no Instagram — Agente Notícias

Publica cada notícia de Mogi Guaçu das edições (6h52, 10h52, 15h52) como **um post de imagem por notícia**.

## Contas (via Windsor.ai, conector `instagram`)
- @mogiguacualerta — account id `17841457552030480`
- @direitaonlinemogiguacu — account id `17841411353795737`
- NÃO postar em @posicionamentoparacorretores.

## Fluxo por edição (a Layla envia a foto de cada post)
1. Monta a edição normalmente (skill `resumir-noticias-mogi-guacu`) e envia o e-mail.
2. Para cada notícia, prepara o **rascunho do post**: manchete, chapéu, destaque, linha fina e legenda próprios de cada conta (ver "Textos diferentes por conta").
3. Gera uma prévia da arte com a cena ilustrada do tema (`node bot-instagram/renderizar.js`) e manda no chat, numerada, em uma seção "Posts prontos — envie a foto de cada um". Marca quais são de política de Mogi Guaçu ou urgentes.
4. **Espera a Layla enviar a foto** (ex.: "foto do post 2"). Quando chegar, gera a arte final com essa foto de fundo (`"foto": "<caminho>"`, sem recorte) e mostra no chat.
5. Publica:
   - post comum → publica assim que a arte com a foto dela estiver pronta;
   - política de Mogi Guaçu ou urgente → só depois de ela aprovar a arte final no chat ("aprovo").
6. Sem foto enviada, o post **não** é publicado. Rascunhos que ficarem sem foto até a edição seguinte são lembrados uma vez e depois descartados.
7. Publicação: salva as artes em `posts/AAAA-MM-DD/`, faz commit e push, e usa `execute_action` (connector `instagram`, action `create_image_post`):
   - `<arquivo>-alerta.jpg` + legenda do Alerta → conta 17841457552030480 (@mogiguacualerta);
   - `<arquivo>-direita.jpg` + legenda da Direita → conta 17841411353795737 (@direitaonlinemogiguacu);
   - URL pública: `https://raw.githubusercontent.com/laylarraraujo-svg/conectaia/claude/vibrant-sagan-064z2o/agentes/agente-noticias/posts/AAAA-MM-DD/<arquivo>.jpg`.
8. Registra no arquivo da edição o que foi publicado e o que ficou esperando foto.

## Foto de fundo
- A foto é **enviada pela Layla** no chat. O robô usa a imagem inteira, sem recorte (`foto_recorte` só se ela pedir).
- A arte leva o crédito "FOTO: REPRODUÇÃO", como nos dashboards.
- A prévia sem foto usa a cena ilustrada do tema.

## Textos diferentes por conta
Cada conta tem manchete, destaque, linha fina e legenda próprios, seguindo a linha editorial do dashboard dela:
- **@mogiguacualerta**: tom jornalístico, direto, sem opinião nem sensacionalismo. Manchete forte (até 80 caracteres). Legenda: 1ª linha com emoji e gancho; 2 a 4 parágrafos curtos (o que, onde, o que muda para o morador); "📍 Mogi Guaçu/SP"; "Siga @mogiguacualerta e ative as notificações 🔔"; 5 a 8 hashtags (#MogiGuaçu #MogiGuacu #MogiGuaçuAlerta…).
- **@direitaonlinemogiguacu**: linha editorial de direita, tom firme, mas fatos exatamente iguais. Manchete em caixa normal (até 85 caracteres); destaque = 2 a 4 primeiras palavras. Legenda: 1ª linha com emoji e gancho; 2 a 4 parágrafos curtos (o que, quem, o que muda); uma pergunta para os comentários; "Siga @direitaonlinemogiguacu e ative as notificações 🔔"; 5 a 8 hashtags (#DireitaOnline #MogiGuaçu…).
- Regras das duas: palavras próprias; não inventar nada; não citar fontes, portais nem @ de outros perfis na legenda; em crime, "suspeito"; não expor vítima nem menor; denúncia não confirmada fica clara ("segundo denúncia", "é acusado de"); sem xingamento.
- Político como fonte: manchete com nome e cargo (ex.: "Vereador Jeferson Luís denuncia…"), e o que ele afirma é "afirma"/"segundo ele".

## Cuidados
- Nunca copiar texto do portal; sempre resumir e citar a fonte.
- Não identificar menores (nome, escola, endereço) nem vítimas de violência.
- Acusação ainda não apurada vai sempre para aprovação.
- Se o Windsor falhar ao publicar, informa no chat e segue com o resto.
