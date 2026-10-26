import argparse
import csv
import json
import time
from collections import Counter
from datetime import datetime
import cv2
from modul.pengaturan import (EXERCISES, FORM_LIMITS, VIS_THRESHOLD, SMOOTH_WINDOW, ERROR_TEXT,
                              BASE_DIR, GAP_RESET_FRAMES, GAP_RESTART_FRAMES, MAX_READ_FAILS)
from modul.deteksi_pose import PoseDetector
from modul.geometri import Smoother
from modul.latihan import (FEATURE_NAMES, compute_features, features_plausible,
                           frame_errors, RepCounter)
from modul.tampilan import draw_hud, show_summary, GREEN, RED, YELLOW


def choose_exercise():
    keys = list(EXERCISES)
    for i, k in enumerate(keys, 1):
        print(f"{i}. {EXERCISES[k]['name']}")
    while True:
        c = input(f"Pilih latihan (1-{len(keys)}): ").strip()
        if c.isdigit() and 1 <= int(c) <= len(keys):
            return keys[int(c) - 1]


def is_live_source(source):
    """Webcam (angka) atau URL kamera = live. Selain itu dianggap file video."""
    return isinstance(source, int) or str(source).startswith(("http://", "https://", "rtsp://"))


def frame_time_ms(cap, live, n_frames, t0):
    """Waktu frame dalam ms. File video: dari nomor frame / FPS video (konsisten, tidak
    tergantung kecepatan komputer). Live: dari jam dinding sejak sesi dimulai."""
    if not live:
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if video_fps and video_fps > 0:
            return int((n_frames - 1) * 1000 / video_fps)
    return int((time.time() - t0) * 1000)


def _r(x):
    return "" if x is None else round(x, 2)


def run_session(exercise, source, show=True, log_path=None):
    cfg = EXERCISES[exercise]
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise IOError(f"Tidak bisa membuka sumber video: {source}")

    live = is_live_source(source)
    detector, smoother, counter = PoseDetector(), Smoother(SMOOTH_WINDOW), RepCounter(exercise)
    flash, flash_color, flash_until = "", GREEN, 0.0
    n_frames, t0, fails, bad_streak, t_sec = 0, time.time(), 0, 0, 0.0

    log_file = log_writer = None
    if log_path:
        log_file = open(log_path, "w", newline="", encoding="utf-8")
        log_writer = csv.writer(log_file)
        log_writer.writerow(["frame", "t_detik", "valid", "sudut_utama_mentah", "in_rep",
                             "jumlah_rep", "error_aktif"] + list(FEATURE_NAMES))

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                if live and fails < MAX_READ_FAILS:   # kamera mungkin belum siap, coba lagi
                    fails += 1
                    time.sleep(0.05)
                    continue
                break
            fails = 0
            n_frames += 1
            ts_ms = frame_time_ms(cap, live, n_frames, t0)
            t_sec = ts_ms / 1000

            landmarks = detector.process(frame, ts_ms)
            points = detector.side_points(landmarks, frame.shape) if landmarks else None
            valid = points is not None and all(points[k][2] > VIS_THRESHOLD for k in cfg["required"])

            f, raw_primary = None, None
            if valid:
                raw = compute_features(points)
                raw_primary = raw[cfg["primary"]]
                if features_plausible(exercise, raw):
                    f = {k: smoother(k, v) for k, v in raw.items()}  # hanya data bersih masuk smoother
                else:
                    valid = False

            angle_val, active = None, []
            if valid:
                bad_streak = 0
                angle_val = f[cfg["primary"]]
                rep, active = counter.update(f, frame_errors(exercise, f), t_sec)

                if rep:
                    if rep["correct"]:
                        flash, flash_color = f"Repetisi {rep['no']} benar!", GREEN
                    else:
                        flash = "Salah: " + ", ".join(ERROR_TEXT[e] for e in rep["errors"])
                        flash_color = RED
                    flash_until = time.time() + 1.5

                if time.time() < flash_until:
                    msg, color = flash, flash_color
                elif not counter.ready:
                    msg, color = "Ambil posisi awal latihan", YELLOW
                elif active:
                    msg, color = ERROR_TEXT[active[0]], RED
                else:
                    msg, color = "Gerakan bagus", GREEN
            else:
                bad_streak += 1
                if bad_streak == GAP_RESET_FRAMES:        # hilang sebentar: buang riwayat lama
                    smoother.reset()
                    counter.reset_streaks()
                if bad_streak == GAP_RESTART_FRAMES:      # hilang lama: mulai dari awal
                    counter.restart()
                    detector.unlock_side()
                if raw_primary is not None:
                    msg, color = "Pose tidak terbaca jelas, coba ubah posisi", YELLOW
                else:
                    msg, color = "Tubuh tidak terlihat penuh, atur kamera dari samping", YELLOW

            if log_writer:
                log_writer.writerow([n_frames, round(t_sec, 3), int(valid), _r(raw_primary),
                                     int(counter.in_rep), len(counter.reps), "|".join(active)]
                                    + [_r(f[k]) if f else "" for k in FEATURE_NAMES])

            if show:
                if landmarks:
                    detector.draw(frame, landmarks)
                n_ok = sum(r["correct"] for r in counter.reps)
                draw_hud(frame, cfg["name"], n_ok, len(counter.reps) - n_ok, angle_val, msg, color)
                cv2.imshow("Pelatih Virtual", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        print("Dihentikan dengan Ctrl+C.")
    finally:
        cap.release()
        if log_file:
            log_file.close()
        if show:
            cv2.destroyAllWindows()

    fps = n_frames / max(time.time() - t0, 1e-6)
    return counter.reps, n_frames, fps, t_sec


def summarize(exercise, reps, fps, durasi):
    errs = Counter(e for r in reps for e in r["errors"])
    n_ok = sum(r["correct"] for r in reps)
    return {"latihan": EXERCISES[exercise]["name"], "total": len(reps), "benar": n_ok,
            "salah": len(reps) - n_ok,
            "kesalahan_terbanyak": errs.most_common(1)[0][0] if errs else None,
            "rincian_kesalahan": dict(errs), "fps": round(fps, 1),
            "durasi_video_detik": round(durasi, 1)}


def main():
    ap = argparse.ArgumentParser(description="Penghitung repetisi dan koreksi gerakan")
    ap.add_argument("--exercise", choices=list(EXERCISES))
    ap.add_argument("--source", default="0", help="indeks kamera, path video, atau URL kamera HP")
    ap.add_argument("--no-display", action="store_true",
                    help="tanpa jendela (untuk memproses video rekaman / evaluasi)")
    ap.add_argument("--log", action="store_true", help="simpan sudut per frame ke CSV di hasil/")
    args = ap.parse_args()

    exercise = args.exercise or choose_exercise()
    source = int(args.source) if args.source.isdigit() else args.source
    show = not args.no_display

    out_dir = BASE_DIR / "hasil"
    out_dir.mkdir(exist_ok=True)
    stamp = f"{datetime.now():%Y%m%d_%H%M%S}"
    log_path = out_dir / f"log_{exercise}_{stamp}.csv" if args.log else None

    reps, n_frames, fps, durasi = run_session(exercise, source, show, log_path)

    if n_frames == 0:
        print("Tidak ada frame yang terbaca (kamera belum siap atau file kosong). Sesi tidak disimpan.")
        if log_path and log_path.exists():
            log_path.unlink()
        return

    summary = summarize(exercise, reps, fps, durasi)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if reps:
        path = out_dir / f"sesi_{exercise}_{stamp}.json"
        data = {"ringkasan": summary, "sumber": str(source),
                "konfigurasi": {"ambang": EXERCISES[exercise], "batas_bentuk": FORM_LIMITS},
                "repetisi": reps}
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
        print(f"Hasil disimpan: {path}")
    else:
        print("Tidak ada repetisi terdeteksi, JSON sesi tidak disimpan.")
    if log_path:
        print(f"Log sudut per frame: {log_path}")

    if show:
        show_summary(summary, ERROR_TEXT)


if __name__ == "__main__":
    main()