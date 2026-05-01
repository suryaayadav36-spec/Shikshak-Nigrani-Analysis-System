# Shikshak Nigrani & Analysis System

A Flask web application for analyzing student performance and predicting dropout risk. The system accepts student academic details, predicts risk using a trained machine learning model, and presents a dashboard with scores, charts, improvement suggestions, recent prediction history, and a downloadable report.

## Project Objective

The goal of this project is to help teachers or mentors identify students who may need academic support early. By checking attendance, marks, assignments, backlogs, and study hours, the app gives a simple risk level and practical suggestions for improvement.

## Features

- Responsive dashboard with sidebar navigation
- Student performance input form with clear example placeholders
- Logistic Regression dropout risk prediction
- Low, Medium, and High risk classification
- Performance score calculation
- Improvement suggestions based on student metrics
- Recent prediction table with colored risk badges
- Downloadable student result report
- Charts for performance profile and risk drivers
- Model summary section on the home page

## Tech Stack

- Python
- Flask
- scikit-learn
- pandas
- NumPy
- HTML
- CSS
- JavaScript
- Chart.js

## Machine Learning Model

The app uses a Logistic Regression model trained on a synthetic student dataset.

Input features:

- Attendance percentage
- Internal marks
- Assignment completion percentage
- Number of backlogs
- Study hours per week

Output:

- Dropout risk prediction
- Risk probability
- Risk level: Low, Medium, or High

The project also includes a rule-based safety check so students with both very low attendance and very low marks are marked as high risk.

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Train the model and generate the dataset:

   ```bash
   python3 model/train_model.py
   ```

4. Run the Flask app:

   ```bash
   python3 app.py
   ```

5. Open the app:

   ```text
   http://127.0.0.1:5001
   ```

## Demo Flow

1. Open the home page and show the dataset/model summary.
2. Go to Add Student.
3. Enter sample student values.
4. Submit the form.
5. Show the dashboard risk result, score, charts, and suggestions.
6. Click Download Report to generate the student report.

## Project Structure

- `app.py` - Flask backend, routes, prediction logic, and report download
- `templates/` - HTML pages
- `static/` - CSS and JavaScript assets
- `model/train_model.py` - synthetic data generation and model training
- `model/model.pkl` - trained model file
- `model/dataset.csv` - generated training dataset
- `requirements.txt` - Python dependencies
