from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = str(BASE_DIR / "model" / "pose_landmarker_full.task")

VIS_THRESHOLD = 0.5
SMOOTH_WINDOW = 5
ERROR_MIN_FRAMES = 5

# --- Pengaturan baru (perbaikan) ---
SIDE_LOCK_FRAMES = 15     # sisi tubuh dikunci setelah sekian frame pertama
GAP_RESET_FRAMES = 3      # tracking hilang sekian frame -> buang riwayat smoothing
GAP_RESTART_FRAMES = 30   # tracking hilang sekian frame -> mulai dari awal (tunggu posisi awal lagi)
MAX_READ_FAILS = 30       # toleransi gagal baca frame untuk kamera live (kamera belum siap)

# Ambang sudut (derajat). Kalibrasi ulang dengan video kelompok.
# min_plausible = sudut terkecil yang masih masuk akal. Sudut di bawahnya dianggap
# kesalahan baca landmark (frame dibuang). Nilainya diturunkan dari data sesi awal:
# push-up normal >= ~50, squat dalam bisa sampai ~18, sit-up >= ~41.
EXERCISES = {
    "pushup": {"name": "Push-up", "primary": "elbow",
               "rest": 155, "start": 140, "partial": 125, "target": 90,
               "min_plausible": 20,
               "partial_error": "pushup_kurang_turun",
               "required": ["shoulder", "elbow", "wrist", "hip", "ankle"]},
    "squat": {"name": "Squat", "primary": "knee",
              "rest": 160, "start": 145, "partial": 135, "target": 100,
              "min_plausible": 10,
              "partial_error": "squat_dangkal",
              "required": ["shoulder", "hip", "knee", "ankle", "foot"]},
    "situp": {"name": "Sit-up", "primary": "hip",
              "rest": 110, "start": 100, "partial": 90, "target": 65,
              "min_plausible": 20,
              "partial_error": "situp_kurang_naik",
              "required": ["shoulder", "hip", "knee", "ankle"]},
}

FORM_LIMITS = {
    "body_line_min": 160,
    "torso_lean_max": 50,
    "knee_toe_max": 0.15,
    "situp_knee_max": 110,
}

ERROR_TEXT = {
    "pinggul_turun": "Pinggul turun, kencangkan perut",
    "pinggul_naik": "Pinggul terlalu tinggi",
    "pushup_kurang_turun": "Push-up kurang turun",
    "squat_dangkal": "Squat kurang dalam",
    "punggung_condong": "Punggung terlalu condong",
    "lutut_lewat_kaki": "Lutut melewati ujung kaki",
    "situp_kurang_naik": "Sit-up kurang naik",
    "kaki_lurus": "Tekuk lutut saat sit-up",
}