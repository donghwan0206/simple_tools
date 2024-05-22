import streamlit as st
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from app.es_api import check_es_url
from datetime import datetime


BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir)
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# ES_URL.txt 파일 경로 설정
resources_path = os.path.join(BASE_DIR, "resources")
st.session_state["resources_path"] = resources_path

# secrets.toml 경로
streamlit_path = os.path.join(BASE_DIR, ".streamlit")
st.session_state["streamlit_path"] = streamlit_path

temp_path = os.path.join(BASE_DIR, "temp")
st.session_state["temp_path"] = temp_path

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, "app.log")

# 핸들러 설정
handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7)
handler.suffix = "%Y-%m-%d"  # 파일 이름에 날짜를 포함하도록 설정
handler.extMatch = r"^\d{4}-\d{2}-\d{2}$"  # 파일 이름의 날짜 형식 설정

# 포매터 설정
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# 로거에 핸들러 추가
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[handler],
)
st.session_state.logging = True

# if st.session_state.logging:
logger = logging.getLogger(__name__)
logger.addHandler(handler)

es_url_file_path = os.path.join(resources_path, "ES_URL.txt")

ui_setup_url = st.empty()
es_url = ""
# 파일 존재 여부 확인
if not os.path.exists(es_url_file_path):

    with ui_setup_url.container():
        # 파일이 없으면 사용자 입력을 통해 URL 값 받기
        st.header("Set up the Elasticsearch URL")
        es_url = st.text_input(
            "Enter the Elasticsearch URL(with port):",
            placeholder="http://localhost:9200",
        )
        if es_url and not es_url.startswith("http"):
            es_url = "http://" + es_url

        logger.info(f"Set up the ES URL: {es_url}")
else:
    # 파일이 있으면 파일에서 URL 값 읽기
    with open(es_url_file_path, "r") as f:
        es_url = f.read().strip()
        logger.info(f"ES URL conf file exists: {es_url}")
# ES_URL 변수에 값 저장
if es_url:  # "ES_URL.txt" 파일 생성 및 URL 값 저장
    ui_setup_url.empty()  # setup_url ui 가리기

    with open(es_url_file_path, "w") as f:
        f.write(es_url)
    if "ES_URL" not in st.session_state:
        st.session_state["ES_URL"] = es_url

    ui_col_left, ui_col_right = st.columns(2)
    with ui_col_left:
        st.subheader("Elasticsearch tools")
        st.write("Elasticsearch URL: ", st.session_state.ES_URL)
        st.page_link("pages/Alias_Switcher.py", label="Alias Switcher", icon="🔀")
        st.page_link("pages/Index_Cleaner.py", label="Index Cleaner", icon="🧹")
        st.page_link(
            "pages/Indexing_PPAUTOCOMPLETE.py",
            label="Indexing PPAUTOCOMPLETE",
            icon="🗳️",
        )

    with ui_col_right:
        st.subheader("DB tools")
        st.page_link(
            "pages/MongoDB_Importer.py",
            label="MongoDB Importer",
            icon="🗄️",
        )
