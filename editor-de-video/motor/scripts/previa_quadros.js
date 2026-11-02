// Prévia quadro a quadro de um projeto montado (python editar.py ... --montar), sem renderizar o vídeo inteiro.
// Abre o index.html da composição no Chromium, coloca o quadro real do vídeo como fundo, avança a linha do tempo GSAP
// até cada instante pedido e tira uma foto. Usa as mesmas regras de visibilidade dos clipes do HyperFrames.
//
// Uso: NODE_PATH=$(npm root -g) node previa_quadros.js <pasta-hf> <pasta-saida> <t1> <t2> ...
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');

(async () => {
  const [hf, saida, ...tempos] = process.argv.slice(2);
  fs.mkdirSync(saida, { recursive: true });
  const html = fs.readFileSync(path.join(hf, 'index.html'), 'utf8');
  const W = +(/data-width="(\d+)"/.exec(html) || [0, 1080])[1];
  const H = +(/data-height="(\d+)"/.exec(html) || [0, 1920])[1];
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage({ viewport: { width: W, height: H } });
  await pagina.addInitScript(() => { window.__timelines = {}; });
  await pagina.goto('file://' + path.resolve(hf, 'index.html'));
  // o runtime do HyperFrames dá a cada .clip uma caixa absoluta de quadro inteiro; a prévia faz o mesmo
  await pagina.addStyleTag({ content: '.clip{position:absolute;left:0;top:0;width:100%;height:100%}#a-roll{position:absolute}' });
  await pagina.evaluate(() => document.fonts.ready);
  for (const t of tempos.map(Number)) {
    const quadro = path.resolve(saida, `_fundo_${t.toFixed(2)}.png`);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(t), '-i', path.join(hf, 'base.mp4'), '-frames:v', '1', quadro]);
    await pagina.evaluate(async ({ t, quadro }) => {
      const v = document.getElementById('a-roll');
      v.removeAttribute('src'); v.poster = 'file://' + quadro + '?' + t; v.load();
      for (const el of document.querySelectorAll('.clip')) {
        if (el.id === 'a-roll') continue;
        const s = +el.dataset.start, d = +el.dataset.duration;
        el.style.visibility = (t >= s && t < s + d) ? 'visible' : 'hidden';
      }
      window.__timelines.main.seek(t, false);
      await new Promise((r) => { const img = new Image(); img.onload = r; img.onerror = r; img.src = v.poster; });
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    }, { t, quadro });
    await pagina.screenshot({ path: path.join(saida, `quadro_${t.toFixed(2)}.png`) });
    fs.unlinkSync(quadro);
  }
  await navegador.close();
})();
