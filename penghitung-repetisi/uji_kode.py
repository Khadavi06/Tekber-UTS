from modul.geometri import angle, angle_to_vertical
from modul.latihan import RepCounter


def cek(nama, hasil, harapan):
    status = "OK" if hasil == harapan else "GAGAL"
    print(f"[{status}] {nama}: hasil={hasil}, harapan={harapan}")


def gerak(atas, bawah, langkah=5):
    return list(range(atas, bawah, -langkah)) + list(range(bawah, atas + langkah, langkah))


def simulasi(exercise, urutan, error=None):
    counter = RepCounter(exercise)
    primary = counter.cfg["primary"]
    for a in urutan:
        counter.update({primary: a}, [error] if error and a < counter.cfg["start"] else [])
    return counter.reps


print("== Geometri ==")
cek("sudut siku-siku", round(angle((1, 0), (0, 0), (0, 1))), 90)
cek("sudut lurus", round(angle((1, 0), (0, 0), (-1, 0))), 180)
cek("badan tegak", round(angle_to_vertical((0, 0), (0, 1))), 0)

print("\n== Squat ==")
reps = simulasi("squat", gerak(170, 80) * 3)
cek("3 squat penuh", (len(reps), sum(r["correct"] for r in reps)), (3, 3))
reps = simulasi("squat", gerak(170, 120))
cek("squat dangkal", reps[0]["errors"] if reps else None, ["squat_dangkal"])
reps = simulasi("squat", gerak(170, 150))
cek("gerakan kecil diabaikan", len(reps), 0)
reps = simulasi("squat", gerak(170, 80), error="punggung_condong")
cek("punggung condong", reps[0]["errors"] if reps else None, ["punggung_condong"])

print("\n== Push-up ==")
reps = simulasi("pushup", gerak(170, 80) * 2)
cek("2 push-up penuh", (len(reps), sum(r["correct"] for r in reps)), (2, 2))
reps = simulasi("pushup", gerak(170, 110))
cek("push-up kurang turun", reps[0]["errors"] if reps else None, ["pushup_kurang_turun"])

print("\n== Sit-up ==")
reps = simulasi("situp", gerak(130, 50) * 2)
cek("2 sit-up penuh", (len(reps), sum(r["correct"] for r in reps)), (2, 2))
reps = simulasi("situp", gerak(130, 80))
cek("sit-up kurang naik", reps[0]["errors"] if reps else None, ["situp_kurang_naik"])