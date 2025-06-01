import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler


def categorize_booked(days):
    if days <= 120:
        return 'short_term'
    elif days <= 240:
        return 'mid_term'
    else:
        return 'long_term'


def make_features(df):
    # 1. 응답률과 수락률 차이 → 호스트의 의사 표현 불일치 탐지
    df['host_response_gap'] = df['host_response_rate'] - df['host_acceptance_rate']
    # 2. 수용 가능 인원 대비 리뷰 수 → 노출도나 만족도 추정
    df['review_density'] = df['number_of_reviews'] / (df['accommodates'] + 1e-5)
    # 3. 최근 리뷰 비율 → 최근에 활발했는지 여부
    df['recent_review_ratio'] = df['number_of_reviews_ltm'] / (df['number_of_reviews'] + 1)
    # 4. 호스트 신뢰도 점수 → 슈퍼호스트 여부 × 응답률
    df['host_activity_score'] = df['host_response_rate'] * df['host_is_superhost']

    # 5. 리뷰 수와 침실 수의 곱 → 숙소 크기 대비 후기 수
    df['reviews_x_beds'] = df['number_of_reviews'] * df['bedrooms']

    # 6. 침실당 수락률 → 단위 공간당 수용 의지
    df['acceptance_per_bed'] = df['host_acceptance_rate'] / (df['bedrooms'] + 1)

    # 7. 월별 리뷰수 × 위생 점수 → 위생 관리와 활발함의 상호작용
    df['monthly_review_score'] = df['reviews_per_month'] * df['has_hygiene_score']

    # 8. 숙면 점수와 작업 공간 점수의 곱 → 업무 친화 숙소 탐지
    df['sleep_x_work'] = df['has_sleep_score'] * df['has_work_score']

    # 9. 리뷰 수 로그 변환 → 정규 분포화
    df['log_reviews'] = np.log1p(df['number_of_reviews'])

    # 10. 침실 로그 변환 → 정규 분포화
    df['log_beds'] = np.log1p(df['bedrooms'])

    # 11. 수용 가능 인원 로그 변환
    df['log_accommodates'] = np.log1p(df['accommodates'])

    # 12. 인기 숙소 여부 → 평균 리뷰 초과 여부
    mean_reviews = df['number_of_reviews'].mean()
    df['is_popular'] = (df['number_of_reviews'] > mean_reviews).astype(int)

    # 13. 수용 인원 구간화 (소형/중형/대형)
    df['size_category'] = pd.cut(df['accommodates'],
                                bins=[0, 2, 4, 10, np.inf],
                                labels=[0, 1, 2, 3])

    df['size_category'] = df['size_category'].astype(int)

    # 14. 침실 수 구간화 (스튜디오, 소형, 중형, 대형)
    df['bedroom_category'] = pd.cut(df['bedrooms'],
                                    bins=[-0.1, 1, 2, 3, np.inf],
                                    labels=[0, 1, 2, 3])

    df['bedroom_category'] = df['bedroom_category'].astype(int)

    # 16. 슈퍼호스트 & 즉시 예약 가능 숙소 → 고품질 숙소 플래그
    df['is_premium'] = ((df['host_is_superhost'] == 1.0) & (df['instant_bookable'] == 1.0)).astype(int)

    # 17. 체크인 편의성 점수 로그 변환 → 값 치우침 보정
    df['log_checkin_score'] = np.log1p(df['has_checkin_score'])

    # 18. 장기 숙박 점수 로그 변환 → 안정적인 장기 숙소 판단
    df['log_longterm_score'] = np.log1p(df['has_longterm_score'])

    # 19. 모든 시설 점수 평균 → 총합적 시설 점수
    facility_scores = [
        'has_basic_score', 'has_safety_score', 'has_hygiene_score',
        'has_cooking_score', 'has_sleep_score', 'has_appliances_score',
        'has_work_score', 'has_checkin_score', 'has_pet_score', 'has_longterm_score'
    ]
    df['avg_facility_score'] = df[facility_scores].mean(axis=1)

    # 20. 시설 점수 총합 → 극단적 고성능 숙소 여부
    df['sum_facility_score'] = df[facility_scores].sum(axis=1)
    
    return df
    

def scale_X(df):
    X = df.drop(columns=['booked', 'id', 'listing_id', 'booked_group', 'fee_before', 'fee_after'])    # 타겟 나중에 넣어야 됨

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled

def load_predict_model():
    with open(file='models/rf_model_best.pkl', mode='rb') as f:
        rf_loaded_model = pickle.load(f)
    return rf_loaded_model


def load_data(path='assets/inside_airbnb_merged_final_data.csv'):
    df = pd.read_csv(path)
    return df

def predict_booked_days(df):
    df = make_features(df)
    X_scaled = scale_X(df)
    model = load_predict_model()

    y_pred = model.predict(X_scaled)
    df['booked_new'] = y_pred
    return df

