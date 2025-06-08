import pandas as pd
import numpy as np
import pickle
import gdown
import os


def make_features(df):
    df['host_response_gap'] = df['host_response_rate'] - df['host_acceptance_rate']
    df['review_density'] = df['number_of_reviews'] / (df['accommodates'] + 1e-5)
    df['recent_review_ratio'] = df['number_of_reviews_ltm'] / (df['number_of_reviews'] + 1)
    df['host_activity_score'] = df['host_response_rate'] * df['host_is_superhost']
    df['reviews_x_beds'] = df['number_of_reviews'] * df['bedrooms']
    df['acceptance_per_bed'] = df['host_acceptance_rate'] / (df['bedrooms'] + 1)
    df['monthly_review_score'] = df['reviews_per_month'] * df['has_hygiene_score']
    df['sleep_x_work'] = df['has_sleep_score'] * df['has_work_score']
    df['log_reviews'] = np.log1p(df['number_of_reviews'])
    df['log_beds'] = np.log1p(df['bedrooms'])
    df['log_accommodates'] = np.log1p(df['accommodates'])
    df['is_popular'] = (df['number_of_reviews'] > df['number_of_reviews'].mean()).astype(int)
    df['size_category'] = pd.cut(df['accommodates'], bins=[0, 2, 4, 10, np.inf], labels=[0, 1, 2, 3])
    df['bedroom_category'] = pd.cut(df['bedrooms'], bins=[-0.1, 1, 2, 3, np.inf], labels=[0, 1, 2, 3])
    df['is_premium'] = ((df['host_is_superhost'] == 1.0) & (df['instant_bookable'] == 1.0)).astype(int)
    df['log_checkin_score'] = np.log1p(df['has_checkin_score'])
    df['log_longterm_score'] = np.log1p(df['has_longterm_score'])
    facility_scores = [
        'has_basic_score', 'has_safety_score', 'has_hygiene_score',
        'has_cooking_score', 'has_sleep_score', 'has_appliances_score',
        'has_work_score', 'has_checkin_score', 'has_pet_score', 'has_longterm_score']
    df['avg_facility_score'] = df[facility_scores].mean(axis=1)
    df['sum_facility_score'] = df[facility_scores].sum(axis=1)
    return df
    

def scale_X(df, scaler):
    X = df.drop(columns=['booked', 'id', 'listing_id', 'fee_before', 'booked_group', 'fee_rate'])   # 타겟 나중에 넣어야 됨

    X_scaled = scaler.transform(X)
    return X_scaled

def load_predict_model():# 모델 경로 및 Google Drive 파일 ID
    model_path = "models/ensemble_model.pkl" # rf_model_best.pkl"
    file_id = "1bN03Jkdnf2umoCwOW58Gbqt6ORWE13YI"
    url = f"https://drive.google.com/uc?id={file_id}"

    # models 폴더 없으면 생성
    os.makedirs("models", exist_ok=True)

    # 모델 파일 없을 때만 다운로드
    if not os.path.exists(model_path):
        print("📥 모델 다운로드 중...")
        gdown.download(url, model_path, quiet=False)

    with open(model_path, "rb") as f:
        model_bundle = pickle.load(f)
    print("### 모델 번들 : ", model_bundle)
    return model_bundle


def load_data(path='assets/inside_airbnb_merged_final_data.csv'):
    df = pd.read_csv(path)
    return df

def predict_booked_days(df):
    df = make_features(df)
    model_bundle = load_predict_model()
    scaler = model_bundle['scaler']

    X_scaled = scale_X(df, scaler)

    rf = model_bundle["rf"]
    lgbm = model_bundle["lgb"]
    gb = model_bundle["gb"]
    knn = model_bundle["knn"]

    rf_pred = rf.predict(X_scaled)
    lgb_pred = lgbm.predict(X_scaled)
    gb_pred = gb.predict(X_scaled)
    knn_pred = knn.predict(X_scaled)

    df['booked_new'] = (rf_pred * 4 + lgb_pred * 2 + gb_pred * 2 + knn_pred * 2) / 10

    return df

