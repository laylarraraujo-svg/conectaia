# Baixador de Trechos do YouTube

Cole o link, escolha o início e o fim do trecho (barra deslizante, campos de tempo ou botão "📍 atual" do player), escolha MP4 ou MP3 e baixe só aquela parte.

## Requisitos
- Python 3.9+
- `ffmpeg` instalado (`brew install ffmpeg` / `sudo apt install ffmpeg` / `winget install ffmpeg`)
- `pip install -r requirements.txt`

## Usar
```bash
python3 app.py
```
Abra http://localhost:8765. Os arquivos ficam em `downloads/`.

## Observações
- Roda só na sua máquina (127.0.0.1).
- Baixe apenas conteúdo seu ou com permissão; baixar vídeos pode violar os Termos de Uso do YouTube.
- Se parar de funcionar, atualize: `pip install -U yt-dlp`.
- Se o YouTube pedir "confirme que você não é um robô", use os cookies do seu navegador:
  `YT_COOKIES_BROWSER=chrome python3 app.py` (ou `firefox`, `edge`).
