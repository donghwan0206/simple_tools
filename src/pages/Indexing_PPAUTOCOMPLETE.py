import json
import os
import streamlit as st
import pandas as pd
from app.es_api import indexing_ppautocomplete
import logging
from streamlit_ace import st_ace

logger = logging.getLogger(__name__)

st.set_page_config(
    layout="wide",
    page_title="Indexing PPAUTOCOMPLETE",
)


# 경로 설정이 안된 경우 index페이지에서 진행
if "resources_path" not in st.session_state:
    st.switch_page("index.py")

config_path = os.path.join(st.session_state.resources_path, "conf.json")


@st.experimental_dialog("config file is not exist.")
def config_not_exist_dialog():
    # st.code(f"{config_path}")
    # st.write("is not exist")

    config_file = st.file_uploader(
        label="Upload config file",
        type=["json"],
        accept_multiple_files=False,
    )
    if config_file is not None:
        try:
            config = json.loads(str(config_file.getvalue(), "utf-8"))
        except Exception:
            st.switch_page("pages/Indexing_PPAUTOCOMPLETE.py")

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)
    if st.button("confirm"):
        st.switch_page("pages/Indexing_PPAUTOCOMPLETE.py")
        pass


# config 파일이 없는 경우 경고 모달로 경고 이후 index 페이지로 리다이렉트
if not os.path.exists(config_path):
    config_not_exist_dialog()

# config 파일이 정상적으로 있는 경우 UI 출력
else:
    with open(config_path, mode="r") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            config_not_exist_dialog()

    # ppautocomplete만 index만 리스트에 저장
    index_list = list(config["index"].keys())[1:]
    locales = ["KR", "US", "EP", "CN", "JP"]

    ui_tab_indexing, ui_tab_editor = st.tabs(["Indexing", "Edit query"])

    # 색인 UI
    with ui_tab_indexing:
        version = st.text_input("version number", placeholder="9999")
        locale = st.selectbox("locale", locales, key="locale").lower()
        data_df = pd.DataFrame(
            [(a, True) for a in index_list], columns=["index", "select"]
        )

        # ppautocomplete 인덱스를 체크박스와 함께 출력
        ppautocomplete_dataframe = st.data_editor(
            data_df,
            column_config={
                "select": st.column_config.CheckboxColumn("select", default=True)
            },
            # disabled=["alias"],
            hide_index=True,
        )

        if st.button("Start Indexing", type="primary"):
            # 체크된(인덱스를 수행할) 인덱스만 추출
            select_df = ppautocomplete_dataframe[ppautocomplete_dataframe["select"]]
            # 체크된 인덱스가 존재하고, version이 입력된 경우에만 수행
            if len(select_df) > 0 and version != "":
                logger.info(
                    f"version: {version}, locale: {locale}, selected index list : {select_df['index'].to_list()}"
                )

                progress_cnt = 100 % len(select_df)
                progress_bar = st.progress(progress_cnt, text="indexing")
                for _, row in select_df.iterrows():
                    # processing UI 빙글빙글
                    with st.spinner(f"indexing... {row['index']}"):
                        # 색인 수행
                        indexing_ppautocomplete(
                            version=version,
                            index=row["index"],
                            locale=locale,
                            conf=config_path,
                        )
                    progress_cnt += 100 // len(select_df)
                    progress_bar.progress(
                        progress_cnt, text=f"complete... {row['index']}"
                    )
                    logger.info(
                        f"v{version}_{row['index']}_{locale} : complete indexing"
                    )
                progress_bar.progress(100, text="indexing complete")

                st.write(select_df)
            else:
                st.warning("선택된 인덱스가 없거나, 버전이 입력되지 않았습니다.")

    # 쿼리 수정 UI
    with ui_tab_editor:
        target_index = st.selectbox("index", options=index_list)
        target_locale = st.selectbox("locale", options=locales, key="target_locale")

        target_query = config["index"][target_index]["query"][target_locale]
        ui_col_left, ui_col_right = st.columns(2)
        with ui_col_left:
            st.subheader("original query")
            code_container = st.container()
            code_container.code(
                target_query,
                language="sql",
                line_numbers=True,
            )

        with ui_col_right:
            st.subheader("edit query")
            # edited_query = st.text_area(
            #     "code edit",
            #     value=target_query,
            #     label_visibility="collapsed",
            #     height=600,
            # )
            edited_query = st_ace(
                value=target_query,
                language="sql",
                tab_size=2,
                theme="dracula",
            )
            if st.button("save query", type="primary"):
                logger.info(f"{target_index}_{target_locale} is changed")
                logger.info(
                    f"\noriginal query is : \n{target_query} \nnew query is : \n{edited_query}"
                )
                config["index"][target_index]["query"][target_locale] = edited_query
                target_query = config["index"][target_index]["query"][target_locale]
                code_container.empty()
                code_container.divider()
                code_container.write("new query")
                code_container.code(
                    target_query,
                    language="sql",
                    line_numbers=True,
                )

                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
