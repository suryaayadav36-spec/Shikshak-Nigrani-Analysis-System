# Shikshak Nigrani & Analysis System

A complete Flask web application for analyzing student performance and predicting dropout risk.

## Features
- Modern responsive frontend with sidebar navigation
- Student data entry form
- Logistic Regression dropout risk prediction
- Performance score and risk indicator
- Dashboard with progress bars, cards, and charts

## Setup
1. Create and activate a virtual environment (recommended):
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
   python model/train_model.py
   ```
4. Run the Flask app:
   ```bash
   python app.py
   ```
5. Open your browser at `http://127.0.0.1:5000`

## Project structure
- `app.py` - Flask backend and prediction routes
- `templates/` - HTML front-end pages
- `static/` - CSS and JavaScript assets
- `model/train_model.py` - synthetic dataset generation and model training
- `model/model.pkl` - serialized trained model file
- `model/dataset.csv` - generated dataset
