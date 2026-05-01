import csv
import os
import pickle
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

model = None


def load_model():
    global model
    if model is None:
        try:
            with open(MODEL_PATH, "rb") as file:
                model = pickle.load(file)
        except FileNotFoundError:
            model = None
    return model


def get_dataset_summary():
    row_count = 0
    accuracy = None
    model_ready = load_model() is not None
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as csv_file:
                row_count = sum(1 for _ in csv_file) - 1
                row_count = max(row_count, 0)
        except Exception:
            row_count = 0
    if model_ready and row_count > 0:
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
        "model_type": "Logistic Regression",
        "model_ready": model_ready,
        "accuracy": accuracy,
    }


def append_prediction_history(record):
    headers = [
        "timestamp",
        "name",
        "risk_level",
        "risk_probability",
        "performance_score",
        "attendance",
        "marks",
        "assignments",
        "backlogs",
        "study_hours",
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
                "performance_score": record["performance_score"],
                "attendance": record["attendance"],
                "marks": record["marks"],
                "assignments": record["assignments"],
                "backlogs": record["backlogs"],
                "study_hours": record["study_hours"],
            })
    except Exception:
        pass


def load_prediction_history(limit=5):
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as history_file:
            reader = list(csv.DictReader(history_file))
            return [row for row in reader][-limit:][::-1]
    except Exception:
        return []


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
    return np.array([[attendance, marks, assignments, backlogs, study_hours]])


def calculate_performance_score(data):
    attendance = data["attendance"]
    marks = data["marks"]
    assignments = data["assignments"]
    study_hours = data["study_hours"]
    backlogs = data["backlogs"]
    raw_score = (
        attendance * 0.24
        + marks * 0.34
        + assignments * 0.18
        + min(study_hours, 35) * 1.3
        + max(0, 5 - backlogs) * 3.2
    )
    score = min(max(round(raw_score / 1.4, 2), 0), 100)
    return score


def evaluate_risk(data, predicted_prob):
    fallback = data["attendance"] < 60 and data["marks"] < 40
    if fallback:
        return "High", 0.95, "High risk because attendance and internal marks are both critically low."
    if predicted_prob >= 0.7:
        return "High", predicted_prob, "The model flags high dropout risk due to multiple weak academic signals."
    if predicted_prob >= 0.4:
        return "Medium", predicted_prob, "The model detects moderate risk; targeted improvement can reduce the chance of dropout."
    return "Low", predicted_prob, "The model predicts low risk; maintain good attendance and study habits."


def risk_color(risk_level):
    return {
        "Low": "#2ecc71",
        "Medium": "#f1c40f",
        "High": "#e74c3c",
    }.get(risk_level, "#95a5a6")


def generate_suggestions(risk_level, data):
    suggestions = []
    if data["attendance"] < 75:
        suggestions.append("Improve attendance by attending all classes and avoiding unnecessary absences.")
    if data["marks"] < 65:
        suggestions.append("Focus on weak subjects with revision sessions and targeted practice.")
    if data["assignments"] < 80:
        suggestions.append("Complete assignments consistently to build confidence and steady performance.")
    if data["backlogs"] > 0:
        suggestions.append("Plan backlog clearing with a weekly timetable and tutor support.")
    if data["study_hours"] < 15:
        suggestions.append("Increase weekly study hours with short, productive sessions.")
    if not suggestions:
        suggestions.append("Keep up the strong habits and monitor progress regularly.")
    if risk_level == "High" and data["marks"] < 50:
        suggestions.append("Seek help from instructors or mentors to improve weak areas quickly.")
    return suggestions


def build_result(student_name, data, performance_score, risk_level, probability, explanation):
    return {
        "name": student_name,
        "attendance": data["attendance"],
        "marks": data["marks"],
        "assignments": data["assignments"],
        "backlogs": data["backlogs"],
        "study_hours": data["study_hours"],
        "performance_score": performance_score,
        "risk_level": risk_level,
        "risk_probability": round(probability * 100, 1),
        "risk_color": risk_color(risk_level),
        "explanation": explanation,
        "suggestions": generate_suggestions(risk_level, data),
    }


def build_report_text(result):
    suggestions = "\n".join(f"- {suggestion}" for suggestion in result["suggestions"])
    return f"""Shikshak Nigrani & Analysis System
Student Performance Report

Student Name: {result["name"]}
Risk Level: {result["risk_level"]} Risk
Risk Probability: {result["risk_probability"]}%
Performance Score: {result["performance_score"]} / 100

Input Metrics
- Attendance: {result["attendance"]}%
- Internal Marks: {result["marks"]}%
- Assignment Completion: {result["assignments"]}%
- Backlogs: {result["backlogs"]}
- Study Hours per Week: {result["study_hours"]}

Model Explanation
{result["explanation"]}

Improvement Suggestions
{suggestions}
"""


@app.route("/")
def home():
    summary = get_dataset_summary()
    return render_template("index.html", summary=summary)


@app.route("/add")
def add_student():
    return render_template("form.html")


@app.route("/predict", methods=["POST"])
def predict():
    student_name = request.form.get("name", "Student").strip()
    attendance = parse_float(request.form.get("attendance"))
    marks = parse_float(request.form.get("marks"))
    assignments = parse_float(request.form.get("assignments"))
    backlogs = parse_int(request.form.get("backlogs"))
    study_hours = parse_float(request.form.get("study_hours"))

    if not student_name:
        flash("Student name cannot be empty.", "danger")
        return redirect(url_for("add_student"))
    if any(value < 0 for value in [attendance, marks, assignments, backlogs, study_hours]):
        flash("Please enter valid non-negative values for all fields.", "danger")
        return redirect(url_for("add_student"))

    student_data = {
        "attendance": min(max(attendance, 0), 100),
        "marks": min(max(marks, 0), 100),
        "assignments": min(max(assignments, 0), 100),
        "backlogs": min(max(backlogs, 0), 20),
        "study_hours": min(max(study_hours, 0), 80),
    }

    loaded_model = load_model()
    probability = 0.5
    if loaded_model is not None:
        try:
            probability = float(loaded_model.predict_proba(build_feature_vector(**student_data))[0][1])
        except Exception:
            probability = 0.5
    else:
        flash(
            "The prediction model is not trained yet. Run `python model/train_model.py` first.",
            "warning",
        )

    risk_level, probability, explanation = evaluate_risk(student_data, probability)
    performance_score = calculate_performance_score(student_data)
    result = build_result(student_name, student_data, performance_score, risk_level, probability, explanation)
    append_prediction_history(result)
    session["latest_result"] = result
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    result = session.get("latest_result")
    history = load_prediction_history(limit=6)
    return render_template("dashboard.html", result=result, history=history)


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
    app.run(host="127.0.0.1", port=5001, debug=True)
