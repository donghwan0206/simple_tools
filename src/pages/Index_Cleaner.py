import streamlit as st
import pandas as pd
import logging
from app.es_api import (
    get_indices_wo_alias,
    delete_indices,
)

st.set_page_config(
    layout="wide",
    page_title="Index Cleaner",
)


logger = logging.getLogger(__name__)

# 메인 페이지에서 elasticsearch url 셋팅 안하고 오면 메인 페이지로 redirect
if "ES_URL" not in st.session_state:
    st.switch_page("index.py")

# ES URL 설정
ES_URL = st.session_state["ES_URL"]


def reload_index_list():
    if "data_df" in st.session_state:
        st.session_state.pop("data_df")
    status, indices = get_indices_wo_alias(ES_URL)
    if status:
        st.session_state.data_df = pd.DataFrame(
            [(a, False) for a in indices], columns=["index", "select"]
        )
    else:
        st.error("Fail")


@st.experimental_dialog("Delete Index")
def confirm_delete(selected_indices, es_url):
    st.warning(
        "Please double-check the selected index in the right table. Once deleted, it cannot be restored."
    )
    st.write(selected_indices)
    if st.button("confirm"):
        logger.info(f"delete index:{selected_indices}")
        status, resp_list = delete_indices(selected_indices, es_url)
        if status:
            logger.info("Success: delete index")
            st.success("Success")
            reload_index_list()
            st.rerun()
        else:
            st.error("Error")
            st.json(resp_list)
            logger.error(resp_list)


selected_aliases = []

ui_tab_index, ui_tab_dummy = st.tabs(["Index with no alias", "dummy"])
with ui_tab_index:
    ui_col_left, ui_col_right = st.columns(2)
    index_list = []

    if "data_df" not in st.session_state:
        reload_index_list()

    with ui_col_left:
        st.subheader("List of index(with no alias)")
        if st.button("Reload list of index", type="primary"):
            reload_index_list()

        ui_col_left_btn, ui_col_right_btn1, ui_col_right_btn2 = st.columns([4, 1, 1])

        with ui_col_left_btn:
            search_words = st.text_input(label="search", placeholder="e.g. locale")
            search_words = search_words.strip().split(" ")
            search_df = st.session_state.data_df
            for word in search_words:
                search_df = search_df[search_df["index"].str.contains(word, na=False)]

        with ui_col_right_btn1:
            if st.button("Check All"):
                st.session_state.data_df["select"] = True
                st.rerun()
        with ui_col_right_btn2:
            if st.button("Uncheck All"):
                st.session_state.data_df["select"] = False
                st.rerun()

        stdf = st.data_editor(
            search_df,
            column_config={
                "index": st.column_config.TextColumn(width="large"),
                "select": st.column_config.CheckboxColumn("select", width="small"),
            },
            disabled=["index"],
            hide_index=True,
            use_container_width=True,
            key="stdf",
        )

        if st.button("Delete Indices", type="primary"):
            st.warning(
                "Please double-check the selected index in the right table. Once deleted, it cannot be restored."
            )
            selected_indices = stdf[stdf["select"]]["index"].tolist()

            confirm_delete(selected_indices, ES_URL)

    with ui_col_right:
        st.subheader("Selcted index")
        # st.table(stdf)
        st.table(stdf[stdf["select"]]["index"])


# dummy UI
with ui_tab_dummy:
    st.write("dummy")

    ui_col_left, ui_col_right = st.columns(2)
    # 좌측 컬럼 UI
    with ui_col_left:
        st.write("left column")

    # 우측 컬럼 UI
    with ui_col_right:
        st.write("right column")
