import os
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
from joblib import dump
import json
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'traffic_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'traffic_model_xgboost.joblib')
METADATA_PATH = os.path.join(BASE_DIR, 'model_metadata.json')
RANDOM_STATE = 42

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"❌ File tidak ditemukan: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)
print(f"📊 Dataset dimuat: {df.shape[0]} baris, {df.shape[1]} kolom")

if 'datetime' in df.columns:
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df['hour'] = df['datetime'].dt.hour
    df['weekday'] = df['datetime'].dt.weekday

feature_candidates = ['distance_km', 'num_segments', 'hour', 'weekday', 'temperature', 'rain']
features = [col for col in feature_candidates if col in df.columns]
target = 'traffic_level'

if target not in df.columns:
    raise ValueError(f"❌ Target '{target}' tidak ada dalam dataset")

if len(features) < 2:
    raise ValueError("❌ Fitur tidak cukup untuk membangun model")

print(f"✅ Fitur digunakan: {features}")

X = df[features]
y = df[target]

imputer = SimpleImputer(strategy='mean')
X = pd.DataFrame(imputer.fit_transform(X), columns=features)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)

print("🔍 Melakukan tuning hyperparameter...")
param_grid = {
    'n_estimators': [100, 200],
    'learning_rate': [0.05, 0.1],
    'max_depth': [3, 5, 7]
}

model = xgb.XGBRegressor(objective='reg:squarederror', random_state=RANDOM_STATE)
grid_search = GridSearchCV(model, param_grid, cv=3, scoring='neg_root_mean_squared_error', n_jobs=-1)
grid_search.fit(X_train, y_train)

best_model = grid_search.best_estimator_
print(f"✅ Model terbaik: {grid_search.best_params_}")

y_pred = best_model.predict(X_test)

from math import sqrt
rmse = sqrt(mean_squared_error(y_test, y_pred))

r2 = r2_score(y_test, y_pred)

print(f"📈 RMSE: {rmse:.2f}")
print(f"📊 R² Score: {r2:.3f}")

dump(best_model, MODEL_PATH)
print(f"💾 Model disimpan: {MODEL_PATH}")

metadata = {
    "timestamp": datetime.datetime.now().isoformat(),
    "model_type": "XGBoost Regressor",
    "features": features,
    "target": target,
    "params": grid_search.best_params_,
    "rmse": rmse,
    "r2_score": r2,
}

with open(METADATA_PATH, 'w') as f:
    json.dump(metadata, f, indent=4)

print(f"📝 Metadata disimpan: {METADATA_PATH}")