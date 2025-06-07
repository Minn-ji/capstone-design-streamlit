import numpy as np
import pandas as pd
from sw_prediction_file import predict_booked_days

def grid_search_optimal_fee(df_raw, fee_range=np.arange(0.00, 0.061, 0.005)):
    best_fee = None
    best_airbnb_revenue = -np.inf
    best_host_revenue = None

    for long_fee in fee_range:
        for mid_fee in fee_range:
            for short_fee in fee_range:
                # ✅ 수수료 책정 기준 만족: short < mid < long
                if not (short_fee < mid_fee < long_fee):
                    continue

                # ✅ 새로운 조건: mid_fee <= 3.3%
                if mid_fee > 0.033:
                    continue

                # ✅ df 복사본 생성
                df_changed = df_raw.copy()

                # ✅ 그룹별 수수료 반영
                fee_map = {
                    'high': short_fee,
                    'mid': mid_fee,
                    'low': long_fee
                }
                df_changed['booked_group'] = pd.cut(df_changed['booked'], bins=[-1, 120, 240, 365], labels=['low', 'mid', 'high'])
                df_changed['fee_rate'] = df_changed['booked_group'].map(fee_map).astype(float).clip(lower=0.0)
                df_changed['fee_before'] = 0.033
                # ✅ 피처 생성 및 정렬
                df_changed = predict_booked_days(df_changed)

                # ✅ 수익 계산
                df_changed['simulated_revenue'] = df_changed['price'] * df_changed['booked_new']
                df_changed['simulated_fee_revenue'] = df_changed['simulated_revenue'] * df_changed['fee_before']
                df_changed['simulated_host_revenue'] = df_changed['simulated_revenue'] - df_changed['simulated_fee_revenue']

                # ✅ 기존 대비 호스트 수익 변화율
                df_changed['original_revenue'] = df_raw['price'] * df_raw['booked']
                df_changed['original_fee_revenue'] = df_changed['original_revenue'] * df_changed['fee_before']
                df_changed['original_host_revenue'] = df_changed['original_revenue'] - df_changed['original_fee_revenue']

                orig_host_total = df_changed['original_host_revenue'].sum()
                sim_host_total = df_changed['simulated_host_revenue'].sum()
                host_delta = (sim_host_total - orig_host_total) / orig_host_total * 100

                # ✅ Airbnb 수익 (총 수수료 수익)
                airbnb_revenue = df_changed['simulated_fee_revenue'].sum()

                # ✅ 조건: 호스트 수익 1.5% 이상 증가 + Airbnb 수익 최대화
                if host_delta >= 1.5 and airbnb_revenue > best_airbnb_revenue:
                    best_airbnb_revenue = airbnb_revenue
                    best_host_revenue = sim_host_total
                    best_fee = (short_fee, mid_fee, long_fee)
                    best_df_changed = df_changed.copy()

    # ✅ 결과 출력
    if best_fee:
        print(f"🏆 최적 수수료 비율 (short, mid, long): "
              f"{round(best_fee[0]*100, 3)}%, {round(best_fee[1]*100, 3)}%, {round(best_fee[2]*100, 3)}%")
        print(f"✅ 최적 Airbnb 수익: ${best_airbnb_revenue:,.0f}")
        print(f"✅ 해당 호스트 수익: ${best_host_revenue:,.0f}")
    else:
        print("❌ 조건을 만족하는 최적 수수료를 찾지 못했습니다.")

    best_fee_map = {
        'high': round(best_fee[0]*100, 3),
        'mid': round(best_fee[1]*100, 3),
        'low': round(best_fee[2]*100, 3)
    }
    return best_fee_map
'''
🏆 최적 수수료 비율 (short, mid, long): 2.5%, 3.0%, 6.0%
✅ 최적 Airbnb 수익: $64,185,188
✅ 해당 호스트 수익: $1,621,710,772

# 앙상블 모델로 바꿨을 때 1 3 5로 나와야 함!!
'''
if __name__ == '__name__':
    df = pd.read_csv('assets/inside_airbnb_merged_final_data.csv')
    grid_search_optimal_fee(df)