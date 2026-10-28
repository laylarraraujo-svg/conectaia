#!/usr/bin/env python3
"""Acha o rosto ao longo do vídeo, para que legendas e textos nunca fiquem na frente dele.

Usa o detector YuNet do OpenCV (models/face_detection_yunet_2023mar.onnx). Amostra alguns quadros por segundo,
guarda a caixa do maior rosto em cada instante (normalizada 0–1) e aumenta a caixa para cobrir testa e cabelo.

Uso:
  python face_track.py video.mp4 -o faces.json [--fps 4]
Saída: {"fps": 4, "boxes": [[t, x0, y0, x1, y1] ou [t, null], ...]}
"""
import argparse
import json
from pathlib import Path

MODEL = Path(__file__).resolve().parent.parent / "models" / "face_detection_yunet_2023mar.onnx"
# quanto aumentar a caixa do detector (fração da altura/largura do rosto): testa/cabelo em cima, queixo embaixo
GROW_TOP, GROW_BOTTOM, GROW_SIDE = 0.30, 0.08, 0.12


def track(video, fps=4.0, min_score=0.6):
    import cv2
    cap = cv2.VideoCapture(str(video))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scale = 480 / max(W, H)                                     # detecta em resolução menor: rápido e suficiente
    w, h = int(W * scale), int(H * scale)
    det = cv2.FaceDetectorYN.create(str(MODEL), "", (w, h), min_score, 0.3, 5)
    step = max(1, round(src_fps / fps))
    boxes, i = [], 0
    while True:
        ok = cap.grab()
        if not ok:
            break
        if i % step == 0:
            ok, frame = cap.retrieve()
            if not ok:
                break
            _, faces = det.detect(cv2.resize(frame, (w, h)))
            t = round(i / src_fps, 3)
            if faces is not None and len(faces):
                x, y, bw, bh = (float(v) for v in max(faces, key=lambda f: f[2] * f[3])[:4])
                x0, x1 = x - bw * GROW_SIDE, x + bw * (1 + GROW_SIDE)
                y0, y1 = y - bh * GROW_TOP, y + bh * (1 + GROW_BOTTOM)
                boxes.append([t, round(max(0, x0 / w), 4), round(max(0, y0 / h), 4),
                              round(min(1, x1 / w), 4), round(min(1, y1 / h), 4)])
            else:
                boxes.append([t, None])
        i += 1
    cap.release()
    return {"fps": fps, "boxes": fill_gaps(boxes)}


def fill_gaps(boxes, max_gap=1.5):
    """Quadros sem detecção (rosto de lado, mão na frente) herdam o rosto vizinho se a falha for curta."""
    out = [b[:] for b in boxes]
    known = [k for k, b in enumerate(out) if b[1] is not None]
    for k, b in enumerate(out):
        if b[1] is not None or not known:
            continue
        near = min(known, key=lambda j: abs(out[j][0] - b[0]))
        if abs(out[near][0] - b[0]) <= max_gap:
            out[k] = [b[0]] + out[near][1:]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--fps", type=float, default=4.0)
    a = ap.parse_args()
    res = track(a.video, a.fps)
    Path(a.output).write_text(json.dumps(res), encoding="utf-8")
    found = sum(1 for b in res["boxes"] if b[1] is not None)
    print(f"Rosto encontrado em {found}/{len(res['boxes'])} amostras -> {a.output}")


if __name__ == "__main__":
    main()
