# 🍽 NAVER 음식 카테고리 + 브랜드 트렌드 분석 (Eddie Final v5)

import streamlit as st
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import os
from datetime import datetime, timedelta

# ------------------------------
#  ✔ 한글 폰트 설정 (리포지토리에 포함된 폰트 사용)
# ------------------------------
font_path = os.path.join(os.path.dirname(__file__), "NanumGothic.ttf")

if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    plt.rc('font', family='NanumGothic')
else:
    # 폰트 파일이 없을 경우 대비
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Noto Sans CJK KR']

plt.rcParams['axes.unicode_minus'] = False


# ------------------------------
#  ✔ Streamlit 페이지 설정
# ------------------------------
st.set_page_config(page_title="🍽 Naver 음식 트렌드 분석", layout="wide")

st.title("🍽 Naver 음식 + 브랜드 검색 트렌드 (한국)")
st.write("NAVER DataLab API 기반으로 브랜드별 검색 트렌드와 점유율을 시각화합니다.")


# ------------------------------
#  ✔ API 키 로드 (Streamlit Cloud Secrets 사용)
# ------------------------------
client_id = st.secrets["NAVER_CLIENT_ID"]
client_secret = st.secrets["NAVER_CLIENT_SECRET"]


# ------------------------------
#  ✔ 음식 카테고리 & 브랜드 정의
# ------------------------------
category_brands = {
    "피자": [
        {"groupName": "피자헛", "keywords": ["피자헛", "피자 헛", "pizzahut"]},
        {"groupName": "도미노피자", "keywords": ["도미노피자", "도미도", "Domino", "Domino's Pizza", "도미노"]},
        {"groupName": "미스터피자", "keywords": ["미스터피자", "Mr피자", "Mr.Pizza"]},
        {"groupName": "피자알볼로", "keywords": ["피자알볼로", "알볼로", "알볼로피자"]},
        {"groupName": "피자나라치킨공주", "keywords": ["피자나라치킨공주", "피자나라 치킨공주", "피치공", "피자나라"]},
        {"groupName": "파파존스피자", "keywords": ["파파존스피자", "파파존스", "Papa John's"]},
        {"groupName": "피자스쿨", "keywords": ["피자스쿨", "피자 스쿨"]},
        {"groupName": "반올림피자", "keywords": ["반올림피자", "반올림", "반올림피자샵"]},
        {"groupName": "청년피자", "keywords": ["청년피자"]},
    ],
    "햄버거": [
        {"groupName": "맥도날드", "keywords": ["맥도날드", "McDonald's", "맥날"]},
        {"groupName": "버거킹", "keywords": ["버거킹", "Burger King"]},
        {"groupName": "롯데리아", "keywords": ["롯데리아", "Lotteria"]},
        {"groupName": "노브랜드버거", "keywords": ["노브랜드버거", "노브랜드 버거", "No Brand Burger"]},
    ],
    "치킨": [
        {"groupName": "교촌치킨", "keywords": ["교촌치킨", "교촌"]},
        {"groupName": "BBQ", "keywords": ["BBQ치킨", "비비큐", "BBQ"]},
        {"groupName": "BHC", "keywords": ["BHC치킨", "비에이치씨", "bhc"]},
        {"groupName": "굽네치킨", "keywords": ["굽네치킨", "굽네"]},
        {"groupName": "푸라닭", "keywords": ["푸라닭", "Puradak"]},
    ],
}


# ------------------------------
#  ✔ 기본 날짜 자동 설정 (어제 ~ 일주일 전)
# ------------------------------
today = datetime.now().date()
end_date_default = today - timedelta(days=1)
start_date_default = today - timedelta(days=7)


# ------------------------------
#  ✔ Streamlit 입력 UI
# ------------------------------
start_date_input = st.date_input(
    "조회 시작일 (YYYY-MM-DD)",
    start_date_default,
    format="YYYY-MM-DD"
)
end_date_input = st.date_input(
    "조회 종료일 (YYYY-MM-DD)",
    end_date_default,
    format="YYYY-MM-DD"
)
start_date = start_date_input.strftime("%Y-%m-%d")
end_date = end_date_input.strftime("%Y-%m-%d")
time_unit = st.selectbox("시간 단위", ["date", "week", "month"], index=0)

selected_categories = st.multiselect(
    "분석할 음식 카테고리 선택",
    list(category_brands.keys()),
    default=["피자"]
)


# ------------------------------
#  ✔ 분석 실행
# ------------------------------
if st.button("🚀 트렌드 분석 실행"):

    keyword_groups = []
    for cat in selected_categories:
        keyword_groups.extend(category_brands[cat])

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json",
    }

    df = pd.DataFrame()
    chunk_size = 5

    with st.spinner("📡 NAVER DataLab에서 데이터 수집 중..."):
        for i in range(0, len(keyword_groups), chunk_size):
            chunk = keyword_groups[i:i+chunk_size]
            body = {
                "startDate": start_date,
                "endDate": end_date,
                "timeUnit": time_unit,
                "keywordGroups": chunk
            }

            response = requests.post(
                "https://openapi.naver.com/v1/datalab/search",
                headers=headers,
                data=json.dumps(body)
            )

            if response.status_code == 200:
                for item in response.json()["results"]:
                    temp = pd.DataFrame(item["data"])
                    temp["keyword"] = item["title"]
                    df = pd.concat([df, temp])
            else:
                st.error(f"❌ 요청 실패: {response.status_code} - {response.text}")

    if df.empty:
        st.error("❌ 데이터가 없습니다. 날짜나 API 설정을 확인하세요.")
    else:
        df.rename(columns={"period": "기간", "ratio": "검색비율"}, inplace=True)
        st.success(f"📊 총 {len(df)}개의 데이터 조회 완료!")

        # ------------------------------
        #  📈 브랜드별 검색 트렌드
        # ------------------------------
        st.subheader("📈 브랜드별 검색 트렌드")
        plt.figure(figsize=(12, 6))

        for cat in selected_categories:
            for brand in category_brands[cat]:
                name = brand["groupName"]
                subset = df[df["keyword"] == name]
                if not subset.empty:
                    plt.plot(subset["기간"], subset["검색비율"], marker=".")
                    plt.text(subset["기간"].iloc[0], subset["검색비율"].iloc[0], f" {name}",
                             bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))

        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)

        # ------------------------------
        #  🏆 평균 검색비율 TOP 10
        # ------------------------------
        st.subheader("🏆 평균 검색비율 TOP 10")
        avg_rank = df.groupby("keyword")["검색비율"].mean().sort_values(ascending=False).reset_index()
        avg_rank.columns = ["브랜드", "평균검색비율"]
        st.table(avg_rank.head(10))

        # ------------------------------
        #  🥧 브랜드별 평균 점유율
        # ------------------------------
        st.subheader("🥧 브랜드별 평균 점유율 (%)")
        brand_avg = df.groupby("keyword")["검색비율"].mean()
        plt.figure(figsize=(4, 4))
        plt.pie(brand_avg, labels=brand_avg.index, autopct="%1.1f%%", startangle=90)
        plt.title("브랜드별 평균 점유율")
        st.pyplot(plt)

        # ------------------------------
        #  📈 최근 4기간 상승률 TOP 5
        # ------------------------------
        st.subheader("📈 최근 4기간 상승률 TOP5")

        df["기간"] = pd.to_datetime(df["기간"])

        growth_list = []
        for brand in df["keyword"].unique():
            temp = df[df["keyword"] == brand].sort_values("기간")
            if len(temp) >= 4:
                recent4 = temp.tail(4)
                first_avg = recent4["검색비율"].iloc[:2].mean()
                last_avg = recent4["검색비율"].iloc[-2:].mean()
                if first_avg > 0:
                    growth = (last_avg - first_avg) / first_avg * 100
                    growth_list.append((brand, growth))

        growth_df = pd.DataFrame(growth_list, columns=["브랜드", "상승률"])
        growth_df = growth_df[growth_df["상승률"] > 0].sort_values("상승률", ascending=False).head(5)

        st.markdown("---")
        st.caption("© 2025 Pizza Hut Korea IT - Eddie Noh 🍕")

        st.table(growth_df)

        # ------------------------------
        #  📋 원본 데이터 출력
        # ------------------------------
        st.markdown("---")
        st.subheader("📋 원본 데이터")
        st.dataframe(df)

# END
