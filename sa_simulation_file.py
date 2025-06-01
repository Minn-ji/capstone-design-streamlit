import pandas as pd

# 2. 변수 수정만 수행하는 함수
def update_columns_by_fee_change(df, fee_dict):
    
    # 예약량 기준 그룹 분류
    df['booked_group'] = pd.cut(df['booked'], bins=[-1, 120, 240, 365], labels=['low', 'mid', 'high'])

    
    df['fee_before'] = 0.033
    df['fee_after'] = df['booked_group'].map(fee_dict).astype(float).clip(lower=0.0)
    fee_delta = (df['fee_after'] - df['fee_before']) * 100 # 수수료 변화 차이

    # 변수 변화량 반영 (기존 열 업데이트)
    base_coefficients = {
        'review_scores_cleanliness': -0.0003,
        'review_scores_communication': -0.0018,
        'review_scores_checkin': -0.002,
        'review_scores_value': -0.0035,
        'number_of_reviews': -0.002
    }

    for col, coef in base_coefficients.items():
        df[col] += coef * fee_delta

    return df

def calculate_revenue(df):
    # 수익 계산
    original_total = (df['price'] * df['booked'] * (3.3/ 100)).sum()
    simulated_total = (df['price'] * df['booked_new'] * (df['fee'].astype(float) / 100)).sum()
    revenue_change = (simulated_total - original_total) / original_total * 100
    return df['booked_new'] * df['price'] * (df['fee'].astype(float) / 100), original_total, simulated_total, revenue_change