// Gera as artes (JPEG 1080x1350) no padrão dos dashboards.
// Uso: node renderizar.js <noticias.json> <pasta_saida>
// noticias.json: [{ "arquivo": "1", "manchete": "...", "linha_fina": "...", "chapeu": "TRÂNSITO",
//                   "destaque": "palavra", "urgente": false, "categoria": "transito" }]
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
      const url = await page.evaluate(x => window.renderizar(x), n);
      const arq = path.join(saida, `${n.arquivo}-${marca}.jpg`);
      fs.writeFileSync(arq, Buffer.from(url.split(",")[1], "base64"));
      console.log(arq);
    }
    await page.close();
  }
  await browser.close();
})();
