import os
import pickle
import numpy as np
import pandas as pd
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.utils import resample

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "model_metrics.json")
FEATURES = ["attendance", "marks", "assignments", "backlogs", "study_hours"]


def create_synthetic_data(rows=7000, high_risk_ratio=0.38, random_state=42):
    rng = np.random.RandomState(random_state)
    pool_size = rows * 4

    attendance = rng.randint(35, 101, pool_size)
    marks = rng.randint(20, 101, pool_size)
    assignments = rng.randint(25, 101, pool_size)
    backlogs = rng.choice([0, 0, 0, 1, 1, 2, 2, 3, 4, 5, 6], pool_size)
    study_hours = rng.randint(3, 41, pool_size)

    risk_score = (
        np.clip(75 - attendance, 0, None) * 0.95
        + np.clip(65 - marks, 0, None) * 0.85
        + np.clip(80 - assignments, 0, None) * 0.35
        + backlogs * 11.5
        + np.clip(15 - study_hours, 0, None) * 1.4
        + ((attendance < 55) & (marks < 50)) * 18
        + ((backlogs >= 3) & (marks < 60)) * 14
        + rng.normal(0, 4.5, pool_size)
    )
    threshold = np.quantile(risk_score, 1 - high_risk_ratio)
    dropout_risk = (risk_score >= threshold).astype(int)

    data = pd.DataFrame(
        {
            "attendance": attendance,
            "marks": marks,
            "assignments": assignments,
            "backlogs": backlogs,
            "study_hours": study_hours,
            "dropout_risk": dropout_risk,
        }
    )

    low_risk_rows = rows - int(rows * high_risk_ratio)
    high_risk_rows = rows - low_risk_rows
    low_risk_df = data[data["dropout_risk"] == 0].sample(low_risk_rows, random_state=random_state)
    high_risk_df = data[data["dropout_risk"] == 1].sample(high_risk_rows, random_state=random_state)
    return pd.concat([low_risk_df, high_risk_df], ignore_index=True).sample(
        frac=1, random_state=random_state
    ).reset_index(drop=True)


def balance_training_data(X_train, y_train, random_state=42):
    train_df = X_train.copy()
    train_df["dropout_risk"] = y_train.values

    majority = train_df[train_df["dropout_risk"] == 0]
    minority = train_df[train_df["dropout_risk"] == 1]
    target_size = max(len(majority), len(minority))

    majority_balanced = resample(majority, replace=True, n_samples=target_size, random_state=random_state)
    minority_balanced = resample(minority, replace=True, n_samples=target_size, random_state=random_state)
    balanced = pd.concat([majority_balanced, minority_balanced]).sample(frac=1, random_state=random_state)

    return balanced[FEATURES], balanced["dropout_risk"]


def train_and_save_model():
    df = create_synthetic_data()
    df.to_csv(DATA_PATH, index=False)

    X = df[FEATURES]
    y = df["dropout_risk"]

    pipeline = Pipeline(
        [
            (
                "model",
                RandomForestClassifier(
                    n_estimators=350,
                    max_depth=10,
                    min_samples_leaf=3,
                    class_weight="balanced_subsample",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.24, random_state=42, stratify=y
    )
    X_train_balanced, y_train_balanced = balance_training_data(X_train, y_train)
    pipeline.fit(X_train_balanced, y_train_balanced)

    predictions = pipeline.predict(X_test)
    score = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    metrics = {
        "model_type": "Random Forest",
        "accuracy": round(float(score), 4),
        "precision_high_risk": round(float(report["1"]["precision"]), 4),
        "recall_high_risk": round(float(report["1"]["recall"]), 4),
        "f1_high_risk": round(float(report["1"]["f1-score"]), 4),
        "class_distribution": {str(k): int(v) for k, v in y.value_counts().sort_index().items()},
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
    }

    print(f"Training complete. Test accuracy: {score:.3f}")
    print(f"High-risk recall: {metrics['recall_high_risk']:.3f}")
    print(f"Saved dataset to {DATA_PATH}")
    print(f"Saving model to {MODEL_PATH}")

    with open(MODEL_PATH, "wb") as file:
        pickle.dump(pipeline, file)
    with open(METRICS_PATH, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)


if __name__ == "__main__":
    train_and_save_model()
