"""Tes logika tanpa kamera. Bisa dijalankan dengan:
    python uji_kode.py            (cetak [OK]/[GAGAL])
    python -m pytest uji_kode.py  (butuh: pip install pytest)
"""
from modul.geometri import angle, angle_to_vertical, Smoother, SideLock
from modul.latihan import RepCounter, features_plausible, frame_errors


def gerak(atas, bawah, langkah=5):
    """Urutan sudut palsu: turun dari `atas` ke `bawah`, lalu naik lagi (1 repetisi)."""
    return list(range(atas, bawah, -langkah)) + list(range(bawah, atas + langkah, langkah))


def simulasi(exercise, urutan, error=None):
    counter = RepCounter(exercise)
    primary = counter.cfg["primary"]
    for a in urutan:
        counter.update({primary: a}, [error] if error and a < counter.cfg["start"] else [])
    return counter.reps


# ---------- Geometri ----------
def test_sudut_siku_siku():
    assert round(angle((1, 0), (0, 0), (0, 1))) == 90


def test_sudut_lurus():
    assert round(angle((1, 0), (0, 0), (-1, 0))) == 180


def test_badan_tegak():
    assert round(angle_to_vertical((0, 0), (0, 1))) == 0


# ---------- Squat ----------
def test_3_squat_penuh():
    reps = simulasi("squat", gerak(170, 80) * 3)
    assert (len(reps), sum(r["correct"] for r in reps)) == (3, 3)


def test_squat_dangkal():
    reps = simulasi("squat", gerak(170, 120))
    assert reps[0]["errors"] == ["squat_dangkal"]


def test_gerakan_kecil_diabaikan():
    assert len(simulasi("squat", gerak(170, 150))) == 0


def test_punggung_condong():
    reps = simulasi("squat", gerak(170, 80), error="punggung_condong")
    assert reps[0]["errors"] == ["punggung_condong"]


# ---------- Push-up ----------
def test_2_pushup_penuh():
    reps = simulasi("pushup", gerak(170, 80) * 2)
    assert (len(reps), sum(r["correct"] for r in reps)) == (2, 2)


def test_pushup_kurang_turun():
    reps = simulasi("pushup", gerak(170, 110))
    assert reps[0]["errors"] == ["pushup_kurang_turun"]


# ---------- Sit-up ----------
def test_2_situp_penuh():
    reps = simulasi("situp", gerak(130, 50) * 2)
    assert (len(reps), sum(r["correct"] for r in reps)) == (2, 2)


def test_situp_kurang_naik():
    reps = simulasi("situp", gerak(130, 80))
    assert reps[0]["errors"] == ["situp_kurang_naik"]


# ---------- Perbaikan baru ----------
def test_smoother_rata_rata():
    s = Smoother(3)
    assert s("a", 3) == 3
    assert s("a", 6) == 4.5
    assert s("a", 9) == 6
    assert s("a", 12) == 9  # jendela 3: (6+9+12)/3


def test_smoother_reset_membuang_riwayat():
    s = Smoother(5)
    s("a", 100)
    s("a", 100)
    s.reset()
    assert s("a", 10) == 10  # tidak tercampur nilai lama


def test_sisi_terkunci_setelah_warmup():
    lock = SideLock(3)
    assert [lock.update(1, 5) for _ in range(3)] == [1, 1, 1]  # terkunci di sisi 1
    assert lock.update(9, 0) == 1                              # data berubah, sisi tetap


def test_sisi_dipilih_ulang_setelah_unlock():
    lock = SideLock(2)
    lock.update(1, 5)
    lock.update(1, 5)
    lock.unlock()
    assert lock.update(9, 0) == 0


def test_outlier_ditolak():
    assert not features_plausible("pushup", {"elbow": 2.0})   # kasus nyata di data sesi
    assert features_plausible("pushup", {"elbow": 54.5})
    assert features_plausible("squat", {"knee": 18.2})        # squat dalam tetap diterima


def test_peringatan_tidak_aktif_sebelum_posisi_awal():
    c = RepCounter("pushup")
    for _ in range(10):  # pengguna masih menekuk (belum di posisi awal), error terus muncul
        rep, active = c.update({"elbow": 100}, ["pinggul_turun"])
    assert active == [] and not c.in_rep and not c.ready
    c.update({"elbow": 170}, [])  # sudah di posisi awal
    assert c.ready


def test_peringatan_aktif_setelah_siap():
    c = RepCounter("pushup")
    c.update({"elbow": 170}, [])
    for _ in range(5):
        rep, active = c.update({"elbow": 100}, ["pinggul_turun"])
    assert active == ["pinggul_turun"]


def test_repetisi_mencatat_waktu():
    c = RepCounter("squat")
    for i, a in enumerate(gerak(170, 80)):
        c.update({"knee": a}, [], t=i * 0.1)
    r = c.reps[0]
    assert 0 <= r["t_mulai"] < r["t_selesai"]


def test_restart_menunggu_posisi_awal_lagi():
    c = RepCounter("squat")
    c.update({"knee": 170}, [])
    c.update({"knee": 120}, [])
    assert c.in_rep
    c.restart()
    assert not c.in_rep and not c.ready


def test_aturan_kesalahan_pushup_dan_squat():
    assert frame_errors("pushup", {"body_line": 150, "hip_offset": 0.2}) == ["pinggul_turun"]
    assert frame_errors("pushup", {"body_line": 150, "hip_offset": -0.2}) == ["pinggul_naik"]
    assert frame_errors("pushup", {"body_line": 175, "hip_offset": 0.0}) == []
    assert "lutut_lewat_kaki" in frame_errors("squat", {"torso_lean": 10, "knee_toe": 0.3})


if __name__ == "__main__":
    gagal = 0
    for nama, fungsi in list(globals().items()):
        if nama.startswith("test_") and callable(fungsi):
            try:
                fungsi()
                print(f"[OK]    {nama}")
            except AssertionError:
                gagal += 1
                print(f"[GAGAL] {nama}")
    print(f"\n{gagal} tes gagal" if gagal else "\nSemua tes lulus")