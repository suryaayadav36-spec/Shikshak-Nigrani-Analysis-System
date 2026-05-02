import csv
import json
import os
import pickle
import socket
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Flask, Response, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "DropoutRiskSecret2026")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "model.pkl")
DATA_PATH = os.path.join(BASE_DIR, "model", "dataset.csv")
HISTORY_PATH = os.path.join(BASE_DIR, "model", "history.csv")
METRICS_PATH = os.path.join(BASE_DIR, "model", "model_metrics.json")
SETTINGS_PATH = os.path.join(BASE_DIR, "model", "settings.json")

model = None

DEFAULT_EVALUATOR_SETTINGS = {
    "risk_low_max": 29,
    "risk_medium_max": 69,
    "target_attendance": 75,
    "target_cpi": 6.0,
    "target_assignments": 80,
    "target_study_hours": 15,
    "target_backlogs": 0,
}


def is_port_available(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def find_available_port(host, preferred_port, attempts=20):
    for port in range(preferred_port, preferred_port + attempts + 1):
        if is_port_available(host, port):
            return port
    raise OSError(f"No available port found from {preferred_port} to {preferred_port + attempts}.")


def load_model():
    global model
    if model is None:
        try:
            with open(MODEL_PATH, "rb") as file:
                model = pickle.load(file)
        except FileNotFoundError:
            model = None
    return model


def load_model_metrics():
    if not os.path.exists(METRICS_PATH):
        return {}
    try:
        with open(METRICS_PATH, "r", encoding="utf-8") as metrics_file:
            return json.load(metrics_file)
    except Exception:
        return {}


def clamp_setting(value, minimum, maximum, default):
    parsed = parse_float(value, default)
    return min(max(parsed, minimum), maximum)


def enrich_evaluator_settings(settings):
    settings["risk_low_max"] = int(settings["risk_low_max"])
    settings["risk_medium_max"] = int(settings["risk_medium_max"])
    settings["risk_medium_min"] = settings["risk_low_max"] + 1
    settings["risk_high_min"] = settings["risk_medium_max"] + 1
    return settings


def load_evaluator_settings():
    settings = dict(DEFAULT_EVALUATOR_SETTINGS)
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as settings_file:
                stored_settings = json.load(settings_file)
                settings.update({key: stored_settings.get(key, value) for key, value in settings.items()})
        except Exception:
            pass

    settings["risk_low_max"] = int(clamp_setting(settings["risk_low_max"], 5, 80, DEFAULT_EVALUATOR_SETTINGS["risk_low_max"]))
    settings["risk_medium_max"] = int(
        clamp_setting(settings["risk_medium_max"], settings["risk_low_max"] + 5, 95, DEFAULT_EVALUATOR_SETTINGS["risk_medium_max"])
    )
    settings["target_attendance"] = round(clamp_setting(settings["target_attendance"], 0, 100, DEFAULT_EVALUATOR_SETTINGS["target_attendance"]), 1)
    settings["target_cpi"] = round(clamp_setting(settings["target_cpi"], 0, 10, DEFAULT_EVALUATOR_SETTINGS["target_cpi"]), 1)
    settings["target_assignments"] = round(clamp_setting(settings["target_assignments"], 0, 100, DEFAULT_EVALUATOR_SETTINGS["target_assignments"]), 1)
    settings["target_study_hours"] = round(clamp_setting(settings["target_study_hours"], 0, 80, DEFAULT_EVALUATOR_SETTINGS["target_study_hours"]), 1)
    settings["target_backlogs"] = int(clamp_setting(settings["target_backlogs"], 0, 20, DEFAULT_EVALUATOR_SETTINGS["target_backlogs"]))
    return enrich_evaluator_settings(settings)


def build_settings_from_form(form):
    low_max = int(clamp_setting(form.get("risk_low_max"), 5, 80, DEFAULT_EVALUATOR_SETTINGS["risk_low_max"]))
    medium_max = int(clamp_setting(form.get("risk_medium_max"), low_max + 5, 95, DEFAULT_EVALUATOR_SETTINGS["risk_medium_max"]))
    settings = {
        "risk_low_max": low_max,
        "risk_medium_max": medium_max,
        "target_attendance": round(clamp_setting(form.get("target_attendance"), 0, 100, DEFAULT_EVALUATOR_SETTINGS["target_attendance"]), 1),
        "target_cpi": round(clamp_setting(form.get("target_cpi"), 0, 10, DEFAULT_EVALUATOR_SETTINGS["target_cpi"]), 1),
        "target_assignments": round(clamp_setting(form.get("target_assignments"), 0, 100, DEFAULT_EVALUATOR_SETTINGS["target_assignments"]), 1),
        "target_study_hours": round(clamp_setting(form.get("target_study_hours"), 0, 80, DEFAULT_EVALUATOR_SETTINGS["target_study_hours"]), 1),
        "target_backlogs": int(clamp_setting(form.get("target_backlogs"), 0, 20, DEFAULT_EVALUATOR_SETTINGS["target_backlogs"])),
    }
    return enrich_evaluator_settings(settings)


def save_evaluator_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    persisted_settings = {key: settings[key] for key in DEFAULT_EVALUATOR_SETTINGS}
    with open(SETTINGS_PATH, "w", encoding="utf-8") as settings_file:
        json.dump(persisted_settings, settings_file, indent=2)


def get_dataset_summary():
    row_count = 0
    accuracy = None
    metrics = load_model_metrics()
    model_ready = load_model() is not None
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as csv_file:
                row_count = sum(1 for _ in csv_file) - 1
                row_count = max(row_count, 0)
        except Exception:
            row_count = 0
    if metrics.get("accuracy") is not None:
        accuracy = float(metrics["accuracy"])
    elif model_ready and row_count > 0:
        try:
            df = pd.read_csv(DATA_PATH)
            X = df[["attendance", "marks", "assignments", "backlogs", "study_hours"]]
            y = df["dropout_risk"]
            loaded_model = load_model()
            accuracy = float(loaded_model.score(X, y))
        except Exception:
            accuracy = None
    return {
        "rows": row_count,
        "features": 5,
        "model_type": metrics.get("model_type", "Random Forest"),
        "model_ready": model_ready,
        "accuracy": accuracy,
        "recall_high_risk": metrics.get("recall_high_risk"),
        "f1_high_risk": metrics.get("f1_high_risk"),
    }


def append_prediction_history(record):
    headers = [
        "timestamp",
        "name",
        "risk_level",
        "risk_probability",
        "risk_score",
        "performance_score",
        "attendance",
        "cpi",
        "marks",
        "assignments",
        "backlogs",
        "study_hours",
        "semester_1_cpi",
        "semester_2_cpi",
        "semester_3_cpi",
    ]
    file_exists = os.path.exists(HISTORY_PATH)
    try:
        with open(HISTORY_PATH, "a", newline="", encoding="utf-8") as history_file:
            writer = csv.DictWriter(history_file, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": record["name"],
                "risk_level": record["risk_level"],
                "risk_probability": record["risk_probability"],
                "risk_score": record["risk_score"],
                "performance_score": record["performance_score"],
                "attendance": record["attendance"],
                "cpi": record["cpi"],
                "marks": record["marks"],
                "assignments": record["assignments"],
                "backlogs": record["backlogs"],
                "study_hours": record["study_hours"],
                "semester_1_cpi": record["semester_1_cpi"],
                "semester_2_cpi": record["semester_2_cpi"],
                "semester_3_cpi": record["semester_3_cpi"],
            })
    except Exception:
        pass


def load_prediction_history(limit=5):
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as history_file:
            reader = [normalize_history_record(row) for row in csv.DictReader(history_file)]
            return [row for row in reader][-limit:][::-1]
    except Exception:
        return []


def load_all_prediction_history():
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as history_file:
            return [normalize_history_record(row) for row in csv.DictReader(history_file)]
    except Exception:
        return []


def normalize_history_record(row):
    normalized = dict(row)
    try:
        cpi = parse_float(normalized.get("cpi"), parse_float(normalized.get("marks")) / 10)
        data = {
            "attendance": parse_float(normalized.get("attendance")),
            "cpi": cpi,
            "marks": parse_float(normalized.get("marks"), cpi * 10),
            "assignments": parse_float(normalized.get("assignments")),
            "backlogs": parse_int(normalized.get("backlogs")),
            "study_hours": parse_float(normalized.get("study_hours")),
            "semester_1_cpi": parse_float(normalized.get("semester_1_cpi"), cpi),
            "semester_2_cpi": parse_float(normalized.get("semester_2_cpi"), cpi),
            "semester_3_cpi": parse_float(normalized.get("semester_3_cpi"), cpi),
        }
        performance_score = calculate_performance_score(data)
        risk_score = calculate_risk_score(data, 0, calculate_risk_drivers(data))
        normalized["cpi"] = cpi
        normalized["performance_score"] = performance_score
        normalized["risk_score"] = risk_score
        normalized["risk_probability"] = risk_score
        normalized["risk_level"] = risk_level_from_score(risk_score)
    except Exception:
        pass
    return normalized


def build_history_analytics(history):
    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    scores = []
    performance_scores = []
    trend_rows = history[-10:]

    for row in history:
        risk_counts[row.get("risk_level", "Medium")] = risk_counts.get(row.get("risk_level", "Medium"), 0) + 1
        scores.append(parse_float(row.get("risk_score")))
        performance_scores.append(parse_float(row.get("performance_score")))

    trend_labels = [
        (row.get("name") or row.get("timestamp") or "Student")[:16]
        for row in trend_rows
    ]
    trend_scores = [parse_float(row.get("risk_score")) for row in trend_rows]

    return {
        "total": len(history),
        "average_risk": round(sum(scores) / len(scores), 1) if scores else 0,
        "average_performance": round(sum(performance_scores) / len(performance_scores), 1)
        if performance_scores
        else 0,
        "high_risk_count": risk_counts.get("High", 0),
        "risk_counts": risk_counts,
        "trend_labels": trend_labels,
        "trend_scores": trend_scores,
    }


def normalize_result_defaults(result):
    if not result:
        return result
    result.setdefault("cpi", round(parse_float(result.get("marks")) / 10, 1))
    result.setdefault("marks", round(parse_float(result.get("cpi")) * 10, 1))
    result.setdefault("semester_1_cpi", result["cpi"])
    result.setdefault("semester_2_cpi", result["cpi"])
    result.setdefault("semester_3_cpi", result["cpi"])
    data = {
        "attendance": parse_float(result.get("attendance")),
        "cpi": parse_float(result.get("cpi")),
        "marks": parse_float(result.get("marks")),
        "assignments": parse_float(result.get("assignments")),
        "backlogs": parse_int(result.get("backlogs")),
        "study_hours": parse_float(result.get("study_hours")),
        "semester_1_cpi": parse_float(result.get("semester_1_cpi")),
        "semester_2_cpi": parse_float(result.get("semester_2_cpi")),
        "semester_3_cpi": parse_float(result.get("semester_3_cpi")),
    }
    performance_score = calculate_performance_score(data)
    risk_drivers = calculate_risk_drivers(data)
    risk_score = calculate_risk_score(data, 0, risk_drivers)
    risk_level = risk_level_from_score(risk_score)
    _, _, _, explanation, explanations, _ = evaluate_risk(data, 0)

    result["performance_score"] = performance_score
    result["risk_score"] = risk_score
    result["risk_probability"] = risk_score
    result["risk_level"] = risk_level
    result["risk_color"] = risk_color(risk_level)
    result["explanation"] = explanation
    result["explanations"] = explanations
    result["risk_drivers"] = risk_drivers
    result["feedback"] = generate_feedback(performance_score, risk_score, data)
    result["suggestions"] = generate_suggestions(risk_level, data)
    result["improvement_plan"] = generate_improvement_plan(data, risk_score, performance_score)
    result["percentile_rank"] = calculate_percentile_rank(performance_score)
    return result


def parse_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_int(value, default=0):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def build_feature_vector(attendance, marks, assignments, backlogs, study_hours):
    return pd.DataFrame(
        [[attendance, marks, assignments, backlogs, study_hours]],
        columns=["attendance", "marks", "assignments", "backlogs", "study_hours"],
    )


def calculate_performance_score(data):
    attendance = data["attendance"]
    cpi_percent = data["cpi"] * 10
    assignments = data["assignments"]
    study_score = clamp((data["study_hours"] / 25) * 100)
    backlog_score = clamp(((5 - data["backlogs"]) / 5) * 100)
    score = (
        attendance * 0.25
        + cpi_percent * 0.35
        + assignments * 0.2
        + study_score * 0.1
        + backlog_score * 0.1
    )
    return round(clamp(score), 2)


def clamp(value, minimum=0, maximum=100):
    return min(max(value, minimum), maximum)


def calculate_risk_drivers(data):
    settings = load_evaluator_settings()
    attendance_target = settings["target_attendance"]
    cpi_target = settings["target_cpi"]
    assignments_target = settings["target_assignments"]
    study_target = settings["target_study_hours"]
    driver_config = [
        {
            "name": "Attendance",
            "weight": 30,
            "value": data["attendance"],
            "risk_value": clamp(((attendance_target - data["attendance"]) / max(attendance_target - 40, 20)) * 100),
            "note": f"Target attendance is at least {attendance_target:g}%; current attendance is {data['attendance']}%.",
        },
        {
            "name": "CPI",
            "weight": 30,
            "value": data["cpi"],
            "risk_value": clamp(((cpi_target - data["cpi"]) / max(cpi_target - 3, 2)) * 100),
            "note": f"Target CPI is at least {cpi_target:g}; current CPI is {data['cpi']}.",
        },
        {
            "name": "Assignments",
            "weight": 20,
            "value": data["assignments"],
            "risk_value": clamp(((assignments_target - data["assignments"]) / max(assignments_target - 30, 20)) * 100),
            "note": f"Target assignment completion is at least {assignments_target:g}%; current completion is {data['assignments']}%.",
        },
        {
            "name": "Backlogs",
            "weight": 10,
            "value": data["backlogs"],
            "risk_value": clamp((data["backlogs"] / 4) * 100),
            "note": f"Backlogs should be cleared quickly; current backlog count is {data['backlogs']}.",
        },
        {
            "name": "Study Hours",
            "weight": 10,
            "value": data["study_hours"],
            "risk_value": clamp(((study_target - data["study_hours"]) / max(study_target - 5, 5)) * 100),
            "note": f"Recommended study time is {study_target:g} hours per week; current study time is {data['study_hours']} hours.",
        },
    ]
    drivers = []
    for driver in driver_config:
        weighted_points = driver["risk_value"] * driver["weight"] / 100
        drivers.append({**driver, "weighted_points": round(weighted_points, 1)})
    return drivers


def calculate_risk_score(data, predicted_prob, drivers):
    settings = load_evaluator_settings()
    performance_score = calculate_performance_score(data)
    risk_score = 100 - performance_score

    if data["attendance"] < max(settings["target_attendance"] - 30, 0):
        risk_score += 25
    elif data["attendance"] < max(settings["target_attendance"] - 15, 0):
        risk_score += 10
    if data["cpi"] < settings["target_cpi"]:
        risk_score += 15
    if data["assignments"] < max(settings["target_assignments"] - 30, 0):
        risk_score += 10
    if data["backlogs"] > 0:
        risk_score += min(data["backlogs"], 5) * 5
    if data["study_hours"] < max(settings["target_study_hours"] - 7, 0):
        risk_score += 10
    if risk_score < 5:
        risk_score = 5
    if performance_score < 75 and risk_score <= settings["risk_low_max"]:
        risk_score = settings["risk_medium_min"]
    if (
        data["backlogs"] >= 4
        or (data["attendance"] < max(settings["target_attendance"] - 25, 0) and data["study_hours"] < settings["target_study_hours"])
        or (data["cpi"] < settings["target_cpi"] and data["assignments"] < settings["target_assignments"])
    ):
        risk_score = max(risk_score, settings["risk_high_min"])
    if performance_score < 50:
        risk_score = min(risk_score, 90)

    return round(clamp(risk_score), 1)


def risk_level_from_score(risk_score):
    settings = load_evaluator_settings()
    if risk_score >= settings["risk_high_min"]:
        return "High"
    if risk_score >= settings["risk_medium_min"]:
        return "Medium"
    return "Low"


def generate_explanations(data, risk_score, drivers):
    settings = load_evaluator_settings()
    explanations = []
    top_drivers = sorted(drivers, key=lambda item: item["weighted_points"], reverse=True)

    for driver in top_drivers:
        if driver["risk_value"] >= 35:
            explanations.append(driver["note"])

    if data["study_hours"] < max(settings["target_study_hours"] - 5, 0) or (
        risk_score >= settings["risk_medium_min"] and data["study_hours"] < settings["target_study_hours"]
    ):
        explanations.append(
            f"Study time is below the recommended {settings['target_study_hours']:g} hours per week; current study time is {data['study_hours']} hours."
        )
    if risk_score >= settings["risk_high_min"] and not explanations:
        explanations.append("The combined model and rule-based score shows a high-risk academic pattern.")
    if not explanations:
        explanations.append("Core academic indicators are within a healthy range; continue monitoring progress.")

    return explanations[:4]


def generate_feedback(performance_score, risk_score, data=None):
    settings = load_evaluator_settings()
    data = data or {}
    attendance = parse_float(data.get("attendance"))
    cpi = parse_float(data.get("cpi"))
    assignments = parse_float(data.get("assignments"))
    backlogs = parse_int(data.get("backlogs"))
    study_hours = parse_float(data.get("study_hours"))
    feedback = []

    if risk_score >= min(settings["risk_high_min"] + 5, 100):
        feedback.append("Teacher alert: student needs immediate academic intervention and weekly monitoring.")
    elif risk_score >= settings["risk_medium_min"]:
        feedback.append("Teacher note: student is manageable, but targeted follow-up is needed before risk increases.")
    elif risk_score <= max(settings["risk_low_max"] - 10, 5) and performance_score >= 75:
        feedback.append("Teacher note: student is currently stable and can be encouraged with enrichment tasks.")
    elif performance_score > 75:
        feedback.append("Teacher note: academic performance is good, with minor habits to strengthen consistency.")
    elif performance_score >= 50:
        feedback.append("Teacher note: effort is visible, but consistency and completion habits need support.")
    else:
        feedback.append("Teacher alert: academic indicators are weak and require structured support.")

    if attendance < settings["target_attendance"]:
        feedback.append(f"Attendance watch: contact the student after two missed classes and guide them toward {settings['target_attendance']:g}% attendance.")
    else:
        feedback.append("Attendance status: attendance is acceptable; keep reinforcing regular class participation.")

    if cpi < settings["target_cpi"]:
        feedback.append(f"Academic support: assign subject-wise revision checkpoints until CPI moves above {settings['target_cpi']:g}.")
    else:
        feedback.append("Academic status: CPI is above the evaluator target; offer practice work to maintain momentum.")

    if assignments < settings["target_assignments"]:
        feedback.append(f"Assignment follow-up: verify pending submissions and set a short deadline to reach {settings['target_assignments']:g}% completion.")
    else:
        feedback.append("Assignment status: submission discipline is healthy; continue periodic checks.")

    if backlogs > settings["target_backlogs"]:
        feedback.append("Backlog action: create a clearing plan with faculty or mentor review every week.")
    elif study_hours < settings["target_study_hours"]:
        feedback.append(f"Study routine: recommend fixed weekly study slots to reach {settings['target_study_hours']:g} hours.")
    else:
        feedback.append("Mentor follow-up: review progress in the next assessment cycle and document improvement.")

    feedback.append("Communication plan: share concise feedback with the student and involve a mentor if the same issue repeats.")
    return feedback


def generate_improvement_plan(data, risk_score, performance_score):
    settings = load_evaluator_settings()
    plan = []

    def add_step(priority, area, action, target):
        plan.append({"priority": priority, "area": area, "action": action, "target": target})

    if data["attendance"] < settings["target_attendance"]:
        add_step(
            "High" if data["attendance"] < max(settings["target_attendance"] - 15, 0) else "Medium",
            "Attendance",
            "Attend regular classes and use remedial sessions to cover missed topics.",
            f"Reach at least {settings['target_attendance']:g}% attendance.",
        )
    elif data["attendance"] < min(settings["target_attendance"] + 10, 100):
        add_step(
            "Low",
            "Attendance",
            "Avoid unnecessary absences and keep attendance steady.",
            f"Stay above {min(settings['target_attendance'] + 10, 100):g}% attendance.",
        )

    if data["cpi"] < settings["target_cpi"]:
        add_step(
            "High",
            "CPI",
            "Revise weak units weekly, solve previous papers, and meet faculty for difficult subjects.",
            f"Raise CPI above {settings['target_cpi']:g}.",
        )
    elif data["cpi"] < min(settings["target_cpi"] + 1, 10):
        add_step(
            "Medium",
            "CPI",
            "Add weekly revision blocks and short tests to stabilize academic performance.",
            f"Move CPI toward {min(settings['target_cpi'] + 1, 10):g}+.",
        )

    if data["assignments"] < settings["target_assignments"]:
        add_step(
            "High" if data["assignments"] < max(settings["target_assignments"] - 30, 0) else "Medium",
            "Assignments",
            "Clear pending submissions first, then follow a fixed weekly submission schedule.",
            f"Maintain {settings['target_assignments']:g}%+ assignment completion.",
        )

    if data["backlogs"] > settings["target_backlogs"]:
        add_step(
            "High" if data["backlogs"] >= 3 else "Medium",
            "Backlogs",
            "Create a backlog clearing timetable and review progress with a mentor every week.",
            f"Reduce backlog count to {settings['target_backlogs']}.",
        )

    if data["study_hours"] < settings["target_study_hours"]:
        add_step(
            "Medium" if risk_score >= settings["risk_medium_min"] else "Low",
            "Study Hours",
            "Add focused study sessions in small daily blocks instead of last-minute preparation.",
            f"Reach {settings['target_study_hours']:g} study hours per week.",
        )

    if not plan:
        add_step(
            "Low",
            "Consistency",
            "Continue the current routine and review progress after every assessment.",
            "Keep risk below 20 and performance above 80.",
        )

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(plan, key=lambda item: priority_order.get(item["priority"], 3))[:5]


def evaluate_risk(data, predicted_prob):
    settings = load_evaluator_settings()
    drivers = calculate_risk_drivers(data)
    risk_score = calculate_risk_score(data, predicted_prob, drivers)
    risk_level = risk_level_from_score(risk_score)
    explanations = generate_explanations(data, risk_score, drivers)

    if risk_level == "High":
        explanation = "High risk: immediate academic support is recommended."
    elif risk_level == "Medium":
        explanation = "Medium risk: targeted intervention can reduce the chance of dropout."
    else:
        explanation = "Low risk: current indicators are mostly stable."

    return risk_level, predicted_prob, risk_score, explanation, explanations, drivers


def risk_color(risk_level):
    return {
        "Low": "#2ecc71",
        "Medium": "#f1c40f",
        "High": "#e74c3c",
    }.get(risk_level, "#95a5a6")


def generate_suggestions(risk_level, data):
    settings = load_evaluator_settings()
    suggestions = []
    if risk_level == "Low":
        if data["attendance"] < min(settings["target_attendance"] + 5, 100):
            suggestions.append(f"Maintain attendance above {min(settings['target_attendance'] + 5, 100):g}% to keep risk low.")
        if data["assignments"] < max(settings["target_assignments"] - 5, 0):
            suggestions.append("Improve assignment completion to strengthen academic consistency.")
        if data["study_hours"] < max(settings["target_study_hours"] - 5, 0):
            suggestions.append("Add a few focused study sessions each week to avoid future risk.")
        if not suggestions:
            suggestions.append("Maintain the current academic pattern and continue regular monitoring.")
        return suggestions

    if data["attendance"] < settings["target_attendance"]:
        suggestions.append(f"Improve attendance to at least {settings['target_attendance']:g}% by attending remedial and regular classes consistently.")
    if data["cpi"] < settings["target_cpi"]:
        suggestions.append(f"Raise CPI above {settings['target_cpi']:g} through weekly revision, practice tests, and faculty follow-up.")
    if data["assignments"] < settings["target_assignments"]:
        suggestions.append(f"Submit pending assignments and maintain at least {settings['target_assignments']:g}% assignment completion.")
    if data["backlogs"] > settings["target_backlogs"]:
        suggestions.append("Plan backlog clearing with a weekly timetable and tutor support.")
    if data["study_hours"] < settings["target_study_hours"]:
        suggestions.append("Increase weekly study hours with short, productive sessions.")
    if not suggestions:
        suggestions.append("Keep up the strong habits and monitor progress regularly.")
    if risk_level == "High":
        suggestions.append("Assign a teacher or mentor follow-up for the next two weeks.")
    return suggestions


def calculate_percentile_rank(performance_score):
    if not os.path.exists(DATA_PATH):
        return None
    try:
        df = pd.read_csv(DATA_PATH)
        scores = []
        for _, row in df.iterrows():
            scores.append(
                calculate_performance_score(
                    {
                        "attendance": parse_float(row.get("attendance")),
                        "cpi": parse_float(row.get("marks")) / 10,
                        "assignments": parse_float(row.get("assignments")),
                        "backlogs": parse_int(row.get("backlogs")),
                        "study_hours": parse_float(row.get("study_hours")),
                    }
                )
            )
        if not scores:
            return None
        below_or_equal = sum(1 for score in scores if score <= performance_score)
        return round((below_or_equal / len(scores)) * 100, 1)
    except Exception:
        return None


def build_result(
    student_name,
    data,
    performance_score,
    risk_level,
    probability,
    risk_score,
    explanation,
    explanations,
    risk_drivers,
):
    return {
        "name": student_name,
        "attendance": data["attendance"],
        "cpi": data["cpi"],
        "marks": data["marks"],
        "assignments": data["assignments"],
        "backlogs": data["backlogs"],
        "study_hours": data["study_hours"],
        "semester_1_cpi": data["semester_1_cpi"],
        "semester_2_cpi": data["semester_2_cpi"],
        "semester_3_cpi": data["semester_3_cpi"],
        "performance_score": performance_score,
        "percentile_rank": calculate_percentile_rank(performance_score),
        "risk_level": risk_level,
        "risk_probability": risk_score,
        "risk_score": risk_score,
        "risk_color": risk_color(risk_level),
        "explanation": explanation,
        "explanations": explanations,
        "risk_drivers": risk_drivers,
        "feedback": generate_feedback(performance_score, risk_score, data),
        "improvement_plan": generate_improvement_plan(data, risk_score, performance_score),
        "suggestions": generate_suggestions(risk_level, data),
    }


def build_report_text(result):
    suggestions = "\n".join(f"- {suggestion}" for suggestion in result["suggestions"])
    explanations = "\n".join(f"- {explanation}" for explanation in result["explanations"])
    feedback = "\n".join(f"- {item}" for item in result["feedback"])
    improvement_plan = "\n".join(
        f"- [{item['priority']}] {item['area']}: {item['action']} Target: {item['target']}"
        for item in result.get("improvement_plan", [])
    )
    drivers = "\n".join(
        f"- {driver['name']}: {driver['weight']}% weight, {driver['weighted_points']} risk points"
        for driver in result["risk_drivers"]
    )
    return f"""Shikshak Nigrani & Analysis System
Student Performance Report

Student Name: {result["name"]}
Risk Level: {result["risk_level"]} Risk
Risk Score: {result["risk_score"]} / 100
Risk Probability: {result["risk_probability"]}%
Performance Score: {result["performance_score"]} / 100

Input Metrics
- Attendance: {result["attendance"]}%
- CPI: {result["cpi"]} / 10
- Assignment Completion: {result["assignments"]}%
- Backlogs: {result["backlogs"]}
- Study Hours per Week: {result["study_hours"]}

Model Explanation
{result["explanation"]}

Automated Feedback
{feedback}

Improvement Plan
{improvement_plan}

Why This Student Is At Risk
{explanations}

Risk Driver Contribution
{drivers}

Improvement Suggestions
{suggestions}
"""


@app.route("/")
def home():
    summary = get_dataset_summary()
    return render_template("index.html", summary=summary)


@app.route("/add")
def add_student():
    settings = load_evaluator_settings()
    return render_template("form.html", settings=settings)


@app.route("/predict", methods=["POST"])
def predict():
    student_name = request.form.get("name", "Student").strip()
    attendance = parse_float(request.form.get("attendance"))
    cpi = parse_float(request.form.get("cpi"))
    assignments = parse_float(request.form.get("assignments"))
    backlogs = parse_int(request.form.get("backlogs"))
    study_hours = parse_float(request.form.get("study_hours"))

    if not student_name:
        flash("Student name cannot be empty.", "danger")
        return redirect(url_for("add_student"))
    if any(value < 0 for value in [attendance, cpi, assignments, backlogs, study_hours]):
        flash("Please enter valid non-negative values for all fields.", "danger")
        return redirect(url_for("add_student"))

    student_data = {
        "attendance": min(max(attendance, 0), 100),
        "cpi": min(max(cpi, 0), 10),
        "marks": min(max(cpi * 10, 0), 100),
        "assignments": min(max(assignments, 0), 100),
        "backlogs": min(max(backlogs, 0), 20),
        "study_hours": min(max(study_hours, 0), 80),
        "semester_1_cpi": min(max(cpi, 0), 10),
        "semester_2_cpi": min(max(cpi, 0), 10),
        "semester_3_cpi": min(max(cpi, 0), 10),
    }

    loaded_model = load_model()
    probability = 0.5
    if loaded_model is not None:
        try:
            probability = float(
                loaded_model.predict_proba(
                    build_feature_vector(
                        student_data["attendance"],
                        student_data["marks"],
                        student_data["assignments"],
                        student_data["backlogs"],
                        student_data["study_hours"],
                    )
                )[0][1]
            )
        except Exception:
            probability = 0.5
    else:
        flash(
            "The prediction model is not trained yet. Run `python model/train_model.py` first.",
            "warning",
        )

    risk_level, probability, risk_score, explanation, explanations, risk_drivers = evaluate_risk(
        student_data, probability
    )
    performance_score = calculate_performance_score(student_data)
    result = build_result(
        student_name,
        student_data,
        performance_score,
        risk_level,
        probability,
        risk_score,
        explanation,
        explanations,
        risk_drivers,
    )
    append_prediction_history(result)
    session["latest_result"] = result
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    result = normalize_result_defaults(session.get("latest_result"))
    history = load_prediction_history(limit=6)
    analytics = build_history_analytics(load_all_prediction_history())
    settings = load_evaluator_settings()
    return render_template("dashboard.html", result=result, history=history, analytics=analytics, settings=settings)


@app.route("/alerts")
def alerts():
    history = load_all_prediction_history()
    at_risk = [
        row for row in history
        if row.get("risk_level") in {"Medium", "High"} or parse_float(row.get("risk_score")) >= 30
    ][::-1]
    analytics = build_history_analytics(history)
    return render_template("alerts.html", at_risk=at_risk, analytics=analytics)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        evaluator_settings = build_settings_from_form(request.form)
        save_evaluator_settings(evaluator_settings)
        if session.get("latest_result"):
            session["latest_result"] = normalize_result_defaults(session["latest_result"])
        flash("Evaluator settings saved. New risk labels and targets will use these values.", "success")
        return redirect(url_for("settings"))
    summary = get_dataset_summary()
    evaluator_settings = load_evaluator_settings()
    return render_template("settings.html", summary=summary, settings=evaluator_settings)


@app.route("/download-report")
def download_report():
    result = session.get("latest_result")
    if not result:
        flash("Generate a prediction before downloading a report.", "warning")
        return redirect(url_for("add_student"))

    filename = f"{result['name'].replace(' ', '_').lower()}_risk_report.txt"
    return Response(
        build_report_text(result),
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    load_model()
    host = os.getenv("HOST", "127.0.0.1")
    preferred_port = int(os.getenv("PORT", os.getenv("FLASK_RUN_PORT", "5001")))
    port = find_available_port(host, preferred_port)
    if port != preferred_port:
        print(f"Port {preferred_port} is in use. Starting on http://{host}:{port} instead.")
    app.run(host=host, port=port, debug=True, use_reloader=False)
