import os
import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")


def create_synthetic_data(rows=220, random_state=42):
    rng = np.random.RandomState(random_state)
    attendance = rng.randint(40, 101, rows)
    marks = rng.randint(25, 101, rows)
    assignments = rng.randint(30, 101, rows)
    backlogs = rng.choice([0, 0, 0, 1, 1, 2, 3, 4, 5], rows)
    study_hours = rng.randint(5, 35, rows)

    risk_score = (
        (100 - attendance) * 0.22
        + (60 - marks).clip(0) * 0.3
        + (40 - assignments).clip(0) * 0.18
        + backlogs * 8
        + (15 - study_hours).clip(0) * 1.2
        + rng.randn(rows) * 5
    )
    dropout_risk = (risk_score > 50).astype(int)

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
    return data


def train_and_save_model():
    df = create_synthetic_data()
    df.to_csv(DATA_PATH, index=False)

    X = df[["attendance", "marks", "assignments", "backlogs", "study_hours"]]
    y = df["dropout_risk"]

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(solver="liblinear", random_state=42)),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.24, random_state=42, stratify=y
    )
    pipeline.fit(X_train, y_train)

    score = pipeline.score(X_test, y_test)
    print(f"Training complete. Test accuracy: {score:.2f}")
    print(f"Saved dataset to {DATA_PATH}")
    print(f"Saving model to {MODEL_PATH}")

    with open(MODEL_PATH, "wb") as file:
        pickle.dump(pipeline, file)


if __name__ == "__main__":
    train_and_save_model()
