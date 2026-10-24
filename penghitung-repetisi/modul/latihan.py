from collections import Counter
from modul.pengaturan import EXERCISES, FORM_LIMITS, ERROR_MIN_FRAMES
from modul.geometri import angle, angle_to_vertical, offset_from_line, dist


def compute_features(p):
    facing = 1 if p["foot"][0] >= p["ankle"][0] else -1
    return {
        "elbow": angle(p["shoulder"], p["elbow"], p["wrist"]),
        "shoulder": angle(p["elbow"], p["shoulder"], p["hip"]),
        "knee": angle(p["hip"], p["knee"], p["ankle"]),
        "hip": angle(p["shoulder"], p["hip"], p["knee"]),
        "body_line": angle(p["shoulder"], p["hip"], p["ankle"]),
        "torso_lean": angle_to_vertical(p["shoulder"], p["hip"]),
        "knee_toe": (p["knee"][0] - p["foot"][0]) * facing / (dist(p["knee"], p["ankle"]) + 1e-6),
        "hip_offset": offset_from_line(p["hip"], p["shoulder"], p["ankle"])
                      / (dist(p["shoulder"], p["hip"]) + 1e-6),
    }


def frame_errors(exercise, f):
    t, e = FORM_LIMITS, []
    if exercise == "pushup":
        if f["body_line"] < t["body_line_min"]:
            e.append("pinggul_turun" if f["hip_offset"] > 0 else "pinggul_naik")
    elif exercise == "squat":
        if f["torso_lean"] > t["torso_lean_max"]:
            e.append("punggung_condong")
        if f["knee_toe"] > t["knee_toe_max"]:
            e.append("lutut_lewat_kaki")
    elif exercise == "situp":
        if f["knee"] > t["situp_knee_max"]:
            e.append("kaki_lurus")
    return e


class RepCounter:
    def __init__(self, exercise):
        self.cfg = EXERCISES[exercise]
        self.in_rep = False
        self.reps = []
        self.streak = Counter()
        self.min_angle = 180.0
        self.rep_errors = set()

    def update(self, f, errors):
        for k in list(self.streak):
            if k not in errors:
                self.streak[k] = 0
        self.streak.update(errors)
        active = [k for k, v in self.streak.items() if v >= ERROR_MIN_FRAMES]

        a = f[self.cfg["primary"]]
        if not self.in_rep:
            if a >= self.cfg["start"]:
                return None, active
            self.in_rep, self.min_angle, self.rep_errors = True, a, set()

        self.min_angle = min(self.min_angle, a)
        self.rep_errors.update(active)
        if a <= self.cfg["rest"]:
            return None, active

        self.in_rep = False
        if self.min_angle > self.cfg["partial"]:
            return None, active

        errs = set(self.rep_errors)
        if self.min_angle > self.cfg["target"]:
            errs.add(self.cfg["partial_error"])
        rep = {"no": len(self.reps) + 1, "min_angle": round(self.min_angle, 1),
               "correct": not errs, "errors": sorted(errs)}
        self.reps.append(rep)
        return rep, active