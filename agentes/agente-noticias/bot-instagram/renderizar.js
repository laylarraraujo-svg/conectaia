// Gera as artes (JPEG 1080x1350) no padrão dos dashboards.
// Uso: node renderizar.js <noticias.json> <pasta_saida>
// noticias.json: [{ "arquivo": "1", "categoria": "transito", "urgente": false,
//   "foto": "caminho/da/foto.jpg", "foto_recorte": 0.6,
//   "alerta":  { "chapeu": "...", "manchete": "...", "destaque": "...", "linha_fina": "..." },
//   "direita": { "chapeu": "...", "manchete": "...", "destaque": "...", "linha_fina": "..." } }]
const { chromium } = require("playwright");
const fs = require("fs"), path = require("path");

(async () => {
  const [, , entrada, saida] = process.argv;
  const noticias = JSON.parse(fs.readFileSync(entrada, "utf8"));
  fs.mkdirSync(saida, { recursive: true });
  const browser = await chromium.launch();
  for (const marca of ["alerta", "direita"]) {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
    await page.goto("file://" + path.join(__dirname, `render-${marca}.html`), { waitUntil: "networkidle" }).catch(() => {});
    for (const n of noticias) {
      const dados = Object.assign({}, n, n[marca] || {});   // textos próprios de cada conta
      if (dados.foto && !dados.foto.startsWith("data:")) {
        dados.foto = "data:image/jpeg;base64," + fs.readFileSync(dados.foto).toString("base64");
      }
      const url = await page.evaluate(x => window.renderizar(x), dados);
      const arq = path.join(saida, `${n.arquivo}-${marca}.jpg`);
      fs.writeFileSync(arq, Buffer.from(url.split(",")[1], "base64"));
      console.log(arq);
    }
    await page.close();
  }
  await browser.close();
})();
