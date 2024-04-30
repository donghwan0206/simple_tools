import streamlit as st
import os

# ES_URL.txt 파일 경로 설정
es_url_file_path = os.path.join(os.path.dirname(__file__), "ES_URL.txt")

# 파일 존재 여부 확인
if not os.path.exists(es_url_file_path):
    # 파일이 없으면 사용자 입력을 통해 URL 값 받기
    st.header("Set up the Elasticsearch URL")
    es_url = st.text_input(
        "Enter the Elasticsearch URL(with port):", placeholder="http://localhost:9200"
    )
    if es_url and not es_url.startswith("http"):
        es_url = "http://" + es_url
else:
    # 파일이 있으면 파일에서 URL 값 읽기
    with open(es_url_file_path, "r") as f:
        es_url = f.read().strip()

# ES_URL 변수에 값 저장
if es_url:  # "ES_URL.txt" 파일 생성 및 URL 값 저장
    with open(es_url_file_path, "w") as f:
        f.write(es_url)
    if "ES_URL" not in st.session_state:
        st.session_state["ES_URL"] = es_url

    # print(f"ES_URL: {ES_URL}")

    st.write("Elasticsearch URL: ", st.session_state.ES_URL)

    st.page_link("pages/alias_switcher.py", label="alias switcher", icon="🔗")
