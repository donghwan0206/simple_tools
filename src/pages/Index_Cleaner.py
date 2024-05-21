import streamlit as st
import pandas as pd
import logging
from app.es_api import (
    get_aliases_via_index_name,
    change_aliases_old_to_new,
    get_all_indices,
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
            logger.info(f"Success delete")
            st.success("Success")
            reload_index_list()
            st.rerun()
        else:
            st.error("Error")
            st.json(resp_list)
            logger.error(resp_list)


selected_aliases = []

ui_tab_alias, ui_tab_dummy = st.tabs(["Index with no alias", "dummy"])
# alias 기반 UI
with ui_tab_alias:
    # Elastic cluster에서 alias list 받아오기
    # logger.info("load alias list")

    # logger.info("complete loading alias list")
    ui_col_left, ui_col_right = st.columns(2)
    index_list = []

    if "data_df" not in st.session_state:
        reload_index_list()

    with ui_col_left:
        st.subheader("List of index(with no alias)")
        ui_col_left_btn, ui_col_right_btn1, ui_col_right_btn2 = st.columns([3, 1, 1])

        with ui_col_left_btn:
            if st.button("Reload list of index", type="primary"):
                reload_index_list()

        with ui_col_right_btn1:
            if st.button("Check All"):
                st.session_state.data_df["select"] = True
                st.rerun()
        with ui_col_right_btn2:
            if st.button("Uncheck All"):
                st.session_state.data_df["select"] = False
                st.rerun()

        stdf = st.data_editor(
            st.session_state.data_df,
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


with ui_tab_dummy:
    # Elastic cluster에서 index list 받아오기
    status, index_list = get_all_indices(ES_URL)

    ui_col_left, ui_col_right = st.columns(2)
    # 좌측 컬럼 UI
    with ui_col_left:
        prev_index_name = st.selectbox(
            "Prev index name",
            index_list,
            index=None,
            placeholder="Select index name...",
        )

        st.markdown(f"Prev Index: `{prev_index_name}`")

        # old_index 선택했을 때만 출력
        if prev_index_name is not None:
            result, resp = get_aliases_via_index_name(
                index_name=prev_index_name, es_url=ES_URL
            )

            # 성공적으로 alias를 받았을 경우(alias가 0 건인 경우도 포함)
            if result:
                data_df = pd.DataFrame(
                    [(a, True) for a in resp], columns=["alias", "select"]
                )
                stdf = st.data_editor(
                    data_df,
                    column_config={
                        "select": st.column_config.CheckboxColumn(
                            "select", default=True
                        )
                    },
                    disabled=["alias"],
                    hide_index=True,
                )

                # 선택된 alias가 있는 경우 표 출력
                if len(stdf) > 0:
                    selected_aliases = stdf[stdf["select"]]["alias"]
                    st.header("selected aliases")
                    st.dataframe(selected_aliases, hide_index=True)
            else:
                st.json(resp)

    # 우측 컬럼 UI
    with ui_col_right:
        new_index_name = st.selectbox(
            "New index name",
            index_list,
            index=None,
            placeholder="Select index name...",
        )
        st.markdown(f"New Index: `{new_index_name}`")

        # 버튼을 누른 경우 실행
        if st.button(label="Change Aliases", type="primary"):
            # 변경할 alias가 선택된 경우만 실행
            if len(selected_aliases) > 0:
                logger.info(
                    f"{selected_aliases.to_list()} change - from: {prev_index_name} ->  to: {new_index_name}"
                )
                result, resp = change_aliases_old_to_new(
                    prev_index_name,
                    new_index_name,
                    selected_aliases,
                    ES_URL,
                )

                st.text(result)
                st.json(resp.text)
            else:
                st.error("old index를 선택하여 변경할 alias를 정해주세요.")
