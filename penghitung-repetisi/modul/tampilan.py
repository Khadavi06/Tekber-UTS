import cv2
import numpy as np

GREEN, RED, YELLOW, WHITE = (0, 200, 0), (0, 0, 255), (0, 215, 255), (255, 255, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_hud(frame, name, n_ok, n_bad, angle_val, message, color):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 95), (40, 40, 40), -1)
    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), color, 8)
    cv2.putText(frame, f"{name}  Benar: {n_ok}  Salah: {n_bad}", (12, 30), FONT, 0.8, WHITE, 2)
    if angle_val is not None:
        cv2.putText(frame, f"Sudut: {angle_val:.0f} deg", (12, 58), FONT, 0.6, WHITE, 1)
    cv2.putText(frame, "q: selesai", (w - 110, 58), FONT, 0.5, WHITE, 1)
    cv2.putText(frame, message, (12, 85), FONT, 0.65, color, 2)


def show_summary(summary, error_text):
    img = np.full((320, 640, 3), 30, np.uint8)
    lines = [f"Latihan          : {summary['latihan']}",
             f"Total repetisi   : {summary['total']}",
             f"Repetisi benar   : {summary['benar']}",
             f"Repetisi salah   : {summary['salah']}",
             f"Kesalahan utama  : {error_text.get(summary['kesalahan_terbanyak'], '-')}",
             f"FPS rata-rata    : {summary['fps']}",
             "Tekan tombol apa saja untuk keluar"]
    for i, line in enumerate(lines):
        cv2.putText(img, line, (20, 45 + i * 40), FONT, 0.65, WHITE, 1)
    cv2.imshow("Ringkasan Sesi", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()