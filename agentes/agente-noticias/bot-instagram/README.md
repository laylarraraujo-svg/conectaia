# Bot de postagem automática no Instagram — Agente Notícias

Publica cada notícia de Mogi Guaçu das edições (6h52, 10h52, 15h52) como **um post de imagem por notícia**.

## Contas (via Windsor.ai, conector `instagram`)
- @mogiguacualerta — account id `17841457552030480`
- @direitaonlinemogiguacu — account id `17841411353795737`
- NÃO postar em @posicionamentoparacorretores.

## Fluxo por edição
1. Monta a edição normalmente (skill `resumir-noticias-mogi-guacu`).
2. Para cada notícia, classifica:
   - **Precisa de aprovação** se for:
     - política de Mogi Guaçu: Prefeitura, prefeito, secretários, Câmara, vereadores, partidos, denúncias contra gestores;
     - urgente: ocorrência em andamento, morte, crime grave recente ou alerta da Defesa Civil.
   - **Publica direto** nos demais casos: obras, serviços, trânsito comum, saúde, empregos, eventos, clima.
3. Gera as artes no **mesmo visual dos dashboards** (DASH NOTÍCIA – MOGI GUAÇU ALERTA e DASH NOTÍCIA – DIREITA ONLINE):
   - `render-alerta.html` e `render-direita.html` usam o código de desenho copiado dos dashboards (logo, cores, cenas por tema).
   - Monte um JSON com `arquivo`, `manchete`, `linha_fina`, `chapeu`, `destaque`, `urgente`, `categoria` e rode `node bot-instagram/renderizar.js <noticias.json> posts/AAAA-MM-DD/`.
   - Sai um JPEG por conta: `<arquivo>-alerta.jpg` (para @mogiguacualerta) e `<arquivo>-direita.jpg` (para @direitaonlinemogiguacu).
   - Se os dashboards mudarem o visual, leia os artifacts de novo e rode `python3 -I bot-instagram/extrair_artes.py <html_alerta> <html_direita>`.
   - Salva em `posts/AAAA-MM-DD/`, faz commit e push no branch `claude/vibrant-sagan-064z2o`.
   - URL pública da imagem: `https://raw.githubusercontent.com/laylarraraujo-svg/conectaia/claude/vibrant-sagan-064z2o/agentes/agente-noticias/posts/AAAA-MM-DD/<arquivo>.jpg` (o repositório é público).
4. Itens que **publicam direto**: `execute_action` connector `instagram`, action `create_image_post`: `<arquivo>-alerta.jpg` + legenda do Alerta na conta 17841457552030480, e `<arquivo>-direita.jpg` + legenda da Direita na conta 17841411353795737.
5. Itens que **precisam de aprovação**: não publica. Lista no chat e no e-mail da edição, em uma seção "Aguardando sua aprovação para o Instagram", com o card e a legenda. Só publica quando a Layla responder no chat aprovando (ex.: "aprovo 1 e 3").
6. Registra no arquivo da edição o que foi publicado (link/ID) e o que ficou aguardando.

## Foto de fundo
- Usa a foto real da notícia: `media_url` (ou `media_thumbnail_url` em vídeo) do post de origem, buscada no Windsor (`instagram_public`). Para matéria do site, a imagem principal da matéria.
- Baixa a foto em pasta temporária e passa em `foto`. O robô recorta a parte de cima (`foto_recorte`, padrão 0.6) para tirar a logo e o texto do portal que ficam embaixo. Confira a arte e ajuste o recorte se ainda aparecer marca de outro perfil.
- A arte leva o crédito "FOTO: REPRODUÇÃO", como nos dashboards.
- Sem foto aproveitável, usa a cena ilustrada do tema.

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
