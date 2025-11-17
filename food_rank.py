# 🍽 NAVER 음식 카테고리 + 브랜드 트렌드 분석 (Eddie Final v4)
import streamlit as st
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform

# ✅ 한글 폰트 설정
if platform.system() == "Windows":
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == "Darwin":
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic')
plt.rcParams['axes.unicode_minus'] = False

# ✅ 페이지 설정
st.set_page_config(page_title="🍽 Naver 음식 트렌드 분석", layout="wide")

# 🏷️ 제목
st.title("🍽 Naver 음식 + 브랜드 검색 트렌드 (한국)")
st.write("NAVER DataLab API 기반으로 브랜드별 검색 트렌드와 점유율을 시각화합니다.")

# 🔑 API 키 설정
client_id = st.secrets["NAVER_CLIENT_ID"]
client_secret = st.secrets["NAVER_CLIENT_SECRET"]

# 🔍 음식 카테고리와 브랜드 매핑
category_brands = {
    "피자": [
        {"groupName": "피자헛", "keywords": ["피자헛", "피자 헛", "pizzahut"]},
        {"groupName": "도미노피자", "keywords": ["도미노피자", "도미도", "Domino", "Domino's Pizza", "도미노"]},
        {"groupName": "미스터피자", "keywords": ["미스터피자", "Mr피자", "Mr.Pizza"]},
        {"groupName": "피자알볼로", "keywords": ["피자알볼로", "알볼로", "알볼로피자"]},
        {"groupName": "7번가피자", "keywords": ["7번가피자", "세븐번가피자", "세븐가피자"]},
        {"groupName": "피자나라치킨공주", "keywords": ["피자나라치킨공주", "피자나라 치킨공주", "피치공"]},
        {"groupName": "파파존스피자", "keywords": ["파파존스피자", "파파존스", "Papa John's"]},
        {"groupName": "피자스쿨", "keywords": ["피자스쿨", "피자 스쿨"]}
    ],
    "햄버거": [
        {"groupName": "맥도날드", "keywords": ["맥도날드", "McDonald's", "맥날"]},
        {"groupName": "버거킹", "keywords": ["버거킹", "Burger King"]},
        {"groupName": "롯데리아", "keywords": ["롯데리아", "Lotteria"]},
        {"groupName": "노브랜드버거", "keywords": ["노브랜드버거", "노브랜드 버거", "No Brand Burger"]}
    ],
    "치킨": [
        {"groupName": "교촌치킨", "keywords": ["교촌치킨", "교촌"]},
        {"groupName": "BBQ", "keywords": ["BBQ치킨", "비비큐", "BBQ"]},
        {"groupName": "BHC", "keywords": ["BHC치킨", "비에이치씨", "bhc"]},
        {"groupName": "굽네치킨", "keywords": ["굽네치킨", "굽네"]},
        {"groupName": "푸라닭", "keywords": ["푸라닭", "Puradak"]}
    ]
}

# 📅 기본 날짜 자동 계산
from datetime import datetime, timedelta
today = datetime.now()
end_date_default = (today - timedelta(days=1)).strftime("%Y-%m-%d")
start_date_default = (today - timedelta(days=7)).strftime("%Y-%m-%d")

# 📅 입력 영역
start_date = st.text_input("조회 시작일 (YYYY-MM-DD)", start_date_default)
end_date = st.text_input("조회 종료일 (YYYY-MM-DD)", end_date_default)
time_unit = st.selectbox("시간 단위", ["date", "week", "month"], index=0)

selected_categories = st.multiselect(
    "분석할 음식 카테고리 선택",
    list(category_brands.keys()),
    default=["피자"]
)

# 🚀 분석 실행
if st.button("🚀 트렌드 분석 실행"):
    keyword_groups = []
    for cat in selected_categories:
        for brand_info in category_brands[cat]:
            keyword_groups.append(brand_info)

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }

    df = pd.DataFrame()
    chunk_size = 5

    with st.spinner("데이터 수집 중..."):
        for i in range(0, len(keyword_groups), chunk_size):
            chunk = keyword_groups[i:i + chunk_size]
            body = {
                "startDate": start_date,
                "endDate": end_date,
                "timeUnit": time_unit,
                "keywordGroups": chunk
            }
            response = requests.post("https://openapi.naver.com/v1/datalab/search",
                                     headers=headers, data=json.dumps(body))
            if response.status_code == 200:
                data = response.json()["results"]
                for item in data:
                    temp = pd.DataFrame(item["data"])
                    temp["keyword"] = item["title"]
                    df = pd.concat([df, temp])
            else:
                st.error(f"⚠️ 요청 실패: {response.status_code} - {response.text}")

    if not df.empty:
        df.rename(columns={"period": "기간", "ratio": "검색비율"}, inplace=True)
        st.success(f"✅ 총 {len(df)}개 항목 데이터 조회 완료!")

        # 📈 브랜드별 검색 트렌드 (좌측 라벨)
        st.subheader("📈 브랜드별 검색 트렌드 (좌측 라벨 표시)")
        plt.figure(figsize=(12, 6))
        for cat in selected_categories:
            for brand_info in category_brands[cat]:
                brand = brand_info["groupName"]
                subset = df[df["keyword"] == brand]
                if not subset.empty:
                    x = subset["기간"]
                    y = subset["검색비율"]
                    plt.plot(x, y, marker=".", linewidth=1.8)
                    # 왼쪽 라벨
                    plt.text(
                        x.iloc[0],
                        y.iloc[0],
                        f" {brand}",
                        fontsize=9,
                        ha='left', va='center',
                        bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1.5)
                    )
        plt.title("브랜드별 검색 트렌드 (NAVER DataLab)")
        plt.ylabel("검색 비율(%)")
        plt.xlabel("기간")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)

        # 🏆 평균 검색비율 TOP10
        st.subheader("🏆 검색 평균 기준 TOP 10")
        avg_rank = df.groupby("keyword")["검색비율"].mean().sort_values(ascending=False).reset_index()
        avg_rank.columns = ["검색어", "평균검색비율"]
        st.table(avg_rank.head(10))

        # 🥧 브랜드별 평균 점유율 (절반 크기로 축소)
        st.subheader("🥧 브랜드별 평균 점유율 (%)")
        brand_avg = df.groupby("keyword")["검색비율"].mean().sort_values(ascending=False).reset_index()
        plt.figure(figsize=(4, 4))  # ✅ 원래 7x7 → 절반 사이즈
        plt.pie(brand_avg["검색비율"], labels=brand_avg["keyword"], autopct="%1.1f%%", startangle=90)
        plt.title("브랜드별 평균 점유율 (소형 차트)")
        st.pyplot(plt)

        # 📈 최근 4기간 상승률 TOP5 (정확히 계산)
        # 🔹 time_unit 값에 따라 단위명 자동 표시
        if time_unit == "date":
            unit_label = "4일간"
        elif time_unit == "week":
            unit_label = "4주간"
        elif time_unit == "month":
            unit_label = "4개월간"
        else:
            unit_label = "4기간"

        st.subheader(f"📈 최근 {unit_label} 상승률 TOP5")

        # 🔹 기간을 날짜형으로 변환 (정렬 오류 방지)
        df["기간"] = pd.to_datetime(df["기간"], errors="coerce")

        growth_data = []
        for brand in df["keyword"].unique():
            temp = df[df["keyword"] == brand].sort_values("기간").reset_index(drop=True)
            if len(temp) >= 4:
                recent = temp.tail(4).copy()
                first_avg = recent["검색비율"].iloc[:2].mean()
                last_avg = recent["검색비율"].iloc[-2:].mean()

                if pd.notnull(first_avg) and pd.notnull(last_avg) and first_avg > 0:
                    growth = ((last_avg - first_avg) / first_avg) * 100
                    growth_data.append({"브랜드": brand, "상승률(%)": round(growth, 2)})

        growth_df = pd.DataFrame(growth_data)
        growth_df = growth_df[growth_df["상승률(%)"] > 0.05]
        growth_df = growth_df.sort_values("상승률(%)", ascending=False).head(5)

        if not growth_df.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            bars = ax.bar(growth_df["브랜드"], growth_df["상승률(%)"], color='tab:blue')
            for bar in bars:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f"{bar.get_height():.1f}%", ha='center', va='bottom', fontsize=9)
            ax.set_title(f"최근 {unit_label} 상승률 TOP5 (평균 기준 상승 브랜드)")
            ax.set_ylabel("상승률(%)")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.warning(f"최근 {unit_label} 동안 유의미하게 상승한 브랜드가 없습니다. (변동이 매우 작거나 일정한 경우)")


        # 📋 원본 데이터 (맨 하단)
        st.markdown("---")
        st.subheader("📋 원본 기간별 검색비율 데이터")
        st.dataframe(df)

    else:
        st.error("❌ 데이터가 없습니다. 날짜나 API 설정을 확인하세요.")

st.markdown("---")
st.caption("© 2025 Pizza Hut Korea IT – Eddie Noh 🍕")
