import argparse
import json
import time
from collections import Counter
from datetime import datetime
import cv2
from modul.pengaturan import EXERCISES, VIS_THRESHOLD, SMOOTH_WINDOW, ERROR_TEXT, BASE_DIR
from modul.deteksi_pose import PoseDetector
from modul.geometri import Smoother
from modul.latihan import compute_features, frame_errors, RepCounter
from modul.tampilan import draw_hud, show_summary, GREEN, RED, YELLOW


def choose_exercise():
    keys = list(EXERCISES)
    for i, k in enumerate(keys, 1):
        print(f"{i}. {EXERCISES[k]['name']}")
    while True:
        c = input(f"Pilih latihan (1-{len(keys)}): ").strip()
        if c.isdigit() and 1 <= int(c) <= len(keys):
            return keys[int(c) - 1]


def run_session(exercise, source):
    cfg = EXERCISES[exercise]
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise IOError(f"Tidak bisa membuka sumber video: {source}")

    detector, smoother, counter = PoseDetector(), Smoother(SMOOTH_WINDOW), RepCounter(exercise)
    flash, flash_color, flash_until = "", GREEN, 0.0
    n_frames, t0 = 0, time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        n_frames += 1

        landmarks = detector.process(frame)
        points = detector.side_points(landmarks, frame.shape) if landmarks else None
        valid = points is not None and all(points[k][2] > VIS_THRESHOLD for k in cfg["required"])

        angle_val = None
        if valid:
            f = {k: smoother(k, v) for k, v in compute_features(points).items()}
            angle_val = f[cfg["primary"]]
            rep, active = counter.update(f, frame_errors(exercise, f))

            if rep:
                if rep["correct"]:
                    flash, flash_color = f"Repetisi {rep['no']} benar!", GREEN
                else:
                    flash = "Salah: " + ", ".join(ERROR_TEXT[e] for e in rep["errors"])
                    flash_color = RED
                flash_until = time.time() + 1.5

            if time.time() < flash_until:
                msg, color = flash, flash_color
            elif active:
                msg, color = ERROR_TEXT[active[0]], RED
            else:
                msg, color = "Gerakan bagus", GREEN
        else:
            msg, color = "Tubuh tidak terlihat penuh, atur kamera dari samping", YELLOW

        if landmarks:
            detector.draw(frame, landmarks)
        n_ok = sum(r["correct"] for r in counter.reps)
        draw_hud(frame, cfg["name"], n_ok, len(counter.reps) - n_ok, angle_val, msg, color)
        cv2.imshow("Pelatih Virtual", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return counter.reps, n_frames / max(time.time() - t0, 1e-6)


def summarize(exercise, reps, fps):
    errs = Counter(e for r in reps for e in r["errors"])
    n_ok = sum(r["correct"] for r in reps)
    return {"latihan": EXERCISES[exercise]["name"], "total": len(reps), "benar": n_ok,
            "salah": len(reps) - n_ok,
            "kesalahan_terbanyak": errs.most_common(1)[0][0] if errs else None,
            "rincian_kesalahan": dict(errs), "fps": round(fps, 1)}


def main():
    ap = argparse.ArgumentParser(description="Penghitung repetisi dan koreksi gerakan")
    ap.add_argument("--exercise", choices=list(EXERCISES))
    ap.add_argument("--source", default="0", help="indeks kamera, path video, atau URL kamera HP")
    args = ap.parse_args()

    exercise = args.exercise or choose_exercise()
    source = int(args.source) if args.source.isdigit() else args.source

    reps, fps = run_session(exercise, source)
    summary = summarize(exercise, reps, fps)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    out_dir = BASE_DIR / "hasil"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"sesi_{exercise}_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"ringkasan": summary, "repetisi": reps}, fp, indent=2, ensure_ascii=False)

    show_summary(summary, ERROR_TEXT)


if __name__ == "__main__":
    main()