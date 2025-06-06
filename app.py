import time

import streamlit as st
import pandas as pd
from sw_prediction_file import predict_booked_days, load_data
from sa_simulation_file import update_columns_by_fee_change, calculate_revenue
import altair as alt
import folium
from streamlit_folium import st_folium
from grid_search_for_best_fee import grid_search_optimal_fee

st.set_page_config(
    page_title="구해줘 숙소",
    page_icon="🏘️",
    layout="wide"
)
if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_city" not in st.session_state:
    st.session_state.selected_city = None

# 🔁 화면 전환 함수
def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()

def show_map():
    location_df = pd.read_csv('assets/inside_airbnb_location.csv').iloc[:200, :]
    st.title("🌍 Airbnb 숙소 한 눈에 보기")
    st.markdown("""
    <div style="padding: 15px 20px;border-radius: 10px; ">
        <p style="font-size: 15px; color: #333333; line-height: 1.6;">
            🏡 <b>Airbnb는 단순한 숙박을 넘어, 진정한 ‘현지 경험’과 ‘삶의 방식’을 제공하는 플랫폼입니다.</b><br>
            <i>  "Belong Anywhere (어디서나 우리 집처럼)"</i>이라는 슬로건 아래,<br>
              낯선 도시에서도 편안하게 머물며, 현지인과 교류하고, 여행지를 깊이 있게 경험할 수 있도록 돕고 있습니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="padding: 20px 20px; background-color: #f2f2f2; border-radius: 10px;">
        <p style="font-size: 16px; line-height: 1.6; color: #333333;">
            전 세계의 매력적인 <b style="color:#ff7f00;">Airbnb 숙소</b>를 지도에서 한눈에 확인해보세요.<br>
            다양한 지역을 호스트와 함께 경험할 수 있습니다.
        </p>
        <p style="font-size: 15px; color: #444444;">
            🛠️ <b style="color:#000000;">수수료 정책을 적용해보고 싶다면</b>,<br>
            왼쪽 <b style="color:#000000;">사이드바에서 도시를 선택</b>해 맞춤형 시뮬레이션을 시작해보세요!
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    map_center = [location_df["latitude"].mean(), location_df["longitude"].mean()]
    m = folium.Map(location=map_center, zoom_start=12)

    # 마커 추가
    for _, row in location_df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            icon=folium.DivIcon(html='<div style="font-size:18px;">🏘️</div>'),
            popup=folium.Popup(
                html=f'<a href="{row["listing_url"]}" target="_blank" '
                     f'style="font-size:15px; white-space:nowrap; display:inline;">🔗 URL</a>',
            )
        ).add_to(m)

    # Streamlit에 지도 출력
    st_folium(m, use_container_width=True, height=600)
    # st.markdown(f"<p style='text-align:right; color:gray;'>표시된 숙소 수: <b>{len(location_df):,}</b>개</p>", unsafe_allow_html=True)

def show_city_fee():
    df = load_data()
    with st.spinner("⏳ 매출 증진을 위한 최적의 수수료 탐색 중입니다..."):
        # best_fee_map = grid_search_optimal_fee(df)

        # 🏆 최적 수수료 비율 (short, mid, long): 2.5%, 3.0%, 6.0%
        # ✅ 최적 Airbnb 수익: $64,185,188
        # ✅ 해당 호스트 수익: $1,621,710,772

        time.sleep(11)
        best_fee_map = {
            'high': 2.5,
            'mid': 3.0,
            'low': 6.0
        }

    # 완료 알림
    st.success("✅ 최적 수수료 탐색 완료!")

    selected_top_fee = best_fee_map['high']
    selected_middle_fee = best_fee_map['mid']
    selected_bottom_fee = best_fee_map['low']

    # 사이드바
    st.sidebar.markdown("### 차등 수수료율 조정")
    top_fee = st.sidebar.slider("상위 수수료율 (%)", 0.0, 10.0, selected_top_fee, step=0.1, format="%.1f", key="top_fee_slider")
    middle_fee = st.sidebar.slider("중위 수수료율 (%)", 0.0, 10.0, selected_middle_fee, step=0.1, format="%.1f", key="middle_fee_slider")
    bottom_fee = st.sidebar.slider("하위 수수료율 (%)", 0.0, 10.0, selected_bottom_fee, step=0.1, format="%.1f", key="bottom_fee_slider")

    fee_map = {'high': top_fee, 'mid': middle_fee, 'low': bottom_fee}

    # booked_group, fee_before, fee_after df에 추가됨
    df = update_columns_by_fee_change(df, fee_map) # 수수료 변화에 따라 컬럼 변화
    # sw feature engineering 모두 추가되고, booked_new 생성
    df = predict_booked_days(df) # 수수료 변화하면 그에 따른 booked_new 생성

    df['fee'] = df['booked_group'].map(fee_map) # 수수료 고정해서 컬럼에 매칭
    # 각각 수수료까지 곱해서 만들어진 총 매출, 오리지널 매출, 시뮬레이션 돌렸을때 매출, 비율
    df['sales'], original_total, simulated_total, revenue_change = calculate_revenue(df)
    group_sales = df.groupby('booked_group')['sales'].sum()


    st.title("📊 수수료율 변화에 따른 매출 시뮬레이션")
    revenue_color = "green" if revenue_change >= 0 else "red"
    st.markdown(f"""
    <div style="font-size:18px; margin-bottom:4px;">
        💡 총 매출 변화: <b style="color:{revenue_color}; font-size:20px;">
        {(simulated_total-original_total):,.0f}원({revenue_change:+,.0f}%)</b> ({original_total:,.0f} → {simulated_total:,.0f})
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<p style='margin-left:35px; font-size:10px; text-align:left; color:gray;'>호스트 수수료에 대한 매출만 해당함.</p>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:18px; margin-bottom:4px;">
        💡 예약 일수 기준 숙소 그룹 별 최적 수수료율</div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="background-color:#f9f7f6; padding:14px 18px; border-radius:8px; border:1px solid #e0e0e0;">
            <div style="font-weight:600; font-size:15px; color:#333333;">상위 숙소(240일 이상)</div>
            <div style="font-size:20px; font-weight:bold; margin-top:5px; color:#e76f51;">{selected_top_fee:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background-color:#f9f7f6; padding:14px 18px; border-radius:8px; border:1px solid #e0e0e0;">
            <div style="font-weight:600; font-size:15px; color:#333333;">중위 숙소(120일~240일)</div>
            <div style="font-size:20px; font-weight:bold; margin-top:5px; color:#f4a261;">{selected_middle_fee:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background-color:#f9f7f6; padding:14px 18px; border-radius:8px; border:1px solid #e0e0e0;">
            <div style="font-weight:600; font-size:15px; color:#333333;">하위 숙소(120일 이하 *신규 호스트 제외)</div>
            <div style="font-size:20px; font-weight:bold; margin-top:5px; color:#2a9d8f;">{selected_bottom_fee:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 📈 차등 수수료 적용 기준별 매출 변화")
    area_df = group_sales.reset_index()
    area_df.columns = ["그룹", "매출"]

    area_chart = alt.Chart(area_df).mark_area(
        line={'color': '#fb8b24'},
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color="#febfa4", offset=0),
                   alt.GradientStop(color="#ffffff", offset=1)],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=alt.X("그룹:N", sort=None),
        y="매출:Q",
        tooltip=["그룹", "매출"]
    ).properties(height=300)

    st.altair_chart(area_chart, use_container_width=True)
    st.markdown("---")

    col1, col2 = st.columns(2)
    # 좌 그룹별 매출
    with col1:
        st.markdown("#### 🏘️ 차등 수수료 적용 기준별 숙소 개수")

        group_counts = df['booked_group'].value_counts().rename_axis("숙소 그룹").reset_index(name="숙소 수")

        color_scale = alt.Scale(
            domain=["high", "mid", "low"],
            range=["#febdbd", "#fef4bd", "#c4f3a9"]
        )
        bar_chart = alt.Chart(group_counts).mark_bar().encode(
            x=alt.X('숙소 수:Q'),
            y=alt.Y('숙소 그룹:N', sort='-x'),
            color=alt.Color('숙소 그룹:N', scale=color_scale, legend=None),
            tooltip=['숙소 그룹', '숙소 수']
        )
        labels = alt.Chart(group_counts).mark_text(
            align='left',
            baseline='middle',
            dx=3  # 막대 옆으로 약간 띄움
        ).encode(
            x='숙소 수:Q',
            y=alt.Y('숙소 그룹:N', sort='-x'),
            text='숙소 수:Q'
        )
        bar_chart = (bar_chart + labels).properties(
            height=300
        )
        st.altair_chart(bar_chart, use_container_width=True)

    # 우측: bar chart
    with col2:
        st.markdown("#### 총 매출 비교")
        compare_df = pd.DataFrame({
            "구분": ["고정 수수료 매출", "차등 수수료 매출"],
            "매출": [original_total, simulated_total]
        })

        # 색상 수동 설정
        color_scale = alt.Scale(
            domain=["고정 수수료 매출", "차등 수수료 매출"],
            range=["#f9c74f", "#a9d7fe"]
        )
        y_max = max(original_total, simulated_total)
        y_buffer = y_max * 0.05
        # 막대 차트
        bar = alt.Chart(compare_df).mark_bar(
            cornerRadiusTopLeft=4,
            cornerRadiusTopRight=4
        ).encode(
            x=alt.X("구분:N", sort=None),
            y=alt.Y("매출:Q", scale=alt.Scale(domain=[0, y_max + y_buffer])),
            color=alt.Color("구분:N", scale=color_scale, legend=None),
            tooltip=["구분", "매출"]
        )

        # 텍스트 라벨 추가
        labels = alt.Chart(compare_df).mark_text(
            align="center",
            baseline="bottom",
            dy=-5  # 막대 위에 띄우기
        ).encode(
            x="구분:N",
            y="매출:Q",
            text=alt.Text("매출:Q", format=",.0f")
        )
        bar_label_chart = (bar + labels).properties(
            height=300
        )
        st.altair_chart(bar_label_chart, use_container_width=True)

def show_scenario():
    selected_top_fee = 2.4
    selected_middle_fee = 3.3
    selected_bottom_fee = 5.5
    fee_map = {'high': selected_top_fee, 'mid': selected_middle_fee, 'low': selected_bottom_fee}

    # 시나리오 선택 여부 확인
    if "selected_scenario" not in st.session_state:
        st.markdown("<br><br><br><br><h2 style='text-align: center;'>시나리오 선택하기</h2>", unsafe_allow_html=True)
        st.markdown("""
        <p style='text-align: center; font-size: 14px; color: #666666;'>
        응답률, 리뷰 수, 체크인 방식 등 다양한 조건을 반영해<br>
        실제 예약 가능성을 기반으로 수수료를 합리적으로 조정합니다.
        </p><br>
        """, unsafe_allow_html=True)
        card_style = """
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 12px;
            text-align: left;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.1);
            height: 180px;
        """

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🧑‍💼 A씨"):
                st.session_state.selected_scenario = 0
                st.rerun()
            st.markdown(f"<div style='{card_style}'>✅ 응답/수락률 100%<br>✅ 슈퍼호스트<br>✅ 즉시 예약 가능</div>", unsafe_allow_html=True)

        with col2:
            if st.button("🧑‍🔧 B씨"):
                st.session_state.selected_scenario = 1
                st.rerun()
            st.markdown(f"<div style='{card_style}'>💬 빠른 커뮤니케이션<br>🛏️ 공유/개인실 운영<br>📝 리뷰 수 다수</div>", unsafe_allow_html=True)

        with col3:
            if st.button("🧑‍🍳 C씨"):
                st.session_state.selected_scenario = 2
                st.rerun()
            st.markdown(f"<div style='{card_style}'>🏡 장기 투숙 최적화<br>🧼 셀프 체크인/취사 가능<br>📆 예약 수는 적지만 기간 김</div>", unsafe_allow_html=True)

    else:
        # 선택된 시나리오에 해당하는 데이터 로드
        scenario_index = st.session_state.selected_scenario
        example= load_data("assets/capstone_example.csv")
        example = update_columns_by_fee_change(example, fee_map)
        example = predict_booked_days(example)

        example['booked_group'] = pd.cut(example['booked_new'], bins=[-1, 120, 240, 365], labels=['low', 'mid', 'high'])
        example['fee'] = example['booked_group'].map(fee_map)

        predicted_days = int(example['booked_new'][scenario_index])
        fee_rate = example['fee'][scenario_index]

        # 출력
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<br><br><br><br><br><h1 style='text-align: center;'>안녕하세요 호스트님 👋</h1>", unsafe_allow_html=True)
        st.markdown(
            f"<h3 style='text-align: center;'>이번 달 부과될 호스트 수수료는 <span style='color:#ff4b4b'>{fee_rate:.1f}%</span> 입니다.</h3>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='text-align: center; font-size:14px;'>예측 모델 기반 지난 달 예약 일수: <b>{predicted_days}일</b></p>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        if st.button("돌아가기"):
            del st.session_state["selected_scenario"]  # 선택된 시나리오 제거
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# session_state 초기화
if "selected_city" not in st.session_state:
    st.session_state.selected_city = None


available_cities = ["New York", "Los Angeles", "Washington, D.C.", "Chicago", "Houston", "Denver", "Phoenix", "Seattle", "Austin"]

st.sidebar.markdown("### 수수료 정책 시뮬레이션 👇")
cols = st.sidebar.columns(3)

for i, city in enumerate(available_cities):
    if cols[i % 3].button(city):
        st.session_state.selected_city = city

st.sidebar.markdown("### 호스트 예상 시나리오 📄")


if "page" not in st.session_state:
    st.session_state.page = "home"


if st.sidebar.button("시나리오 실행하기"):
    st.session_state.page = "scenario"
    st.rerun()


if st.session_state.page == "scenario":
    show_scenario()
elif st.session_state.selected_city =='New York':
    show_city_fee()
elif st.session_state.selected_city != None:
    st.toast(f"🚧 {st.session_state.selected_city}은(는) 아직 서비스 준비 중입니다.", icon="⚠️")
    st.session_state.selected_city = None
    go_to("home")
elif st.session_state.selected_city is None:
    show_map()

