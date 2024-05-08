import streamlit as st
import pandas as pd
import logging
from app.es_api import (
    get_aliases_via_index_name,
    change_aliases_old_to_new,
    get_all_indices,
    get_all_aliases,
    get_indices_via_phrase,
)

logger = logging.getLogger(__name__)

# 메인 페이지에서 elasticsearch url 셋팅 안하고 오면 메인 페이지로 redirect
if "ES_URL" not in st.session_state:
    st.switch_page("index.py")

# ES URL 설정
ES_URL = st.session_state["ES_URL"]

selected_aliases = []

ui_tab_alias, ui_tab_index = st.tabs(["via Alias", "via Index"])

# alias 기반 UI
with ui_tab_alias:
    # Elastic cluster에서 alias list 받아오기
    # logger.info("load alias list")
    status, aliases = get_all_aliases(ES_URL)
    alias_list = aliases.keys()
    # logger.info("complete loading alias list")
    ui_col_left, ui_col_right = st.columns(2)
    index_list = []

    with ui_col_left:
        alias_name = st.selectbox(
            "Select alias",
            alias_list,
            index=None,
            placeholder="Select alias name...",
        )

        st.markdown(f"Selected alias: `{alias_name}`")

        # old_index 선택했을 때만 출력
        if alias_name is not None:
            index_list = aliases[alias_name]
            # 성공적으로 alias를 받았을 경우(alias가 0 건인 경우도 포함)
            if len(index_list) > 0:
                st.table(index_list)
            else:
                st.write("No index")

    with ui_col_right:
        prev_index_name = st.selectbox(
            "prev index name", index_list, placeholder="Select index name..."
        )
        # logger.info(f"selected prev index: {prev_index_name}")

        if prev_index_name is not None:
            _, target_index_list = get_indices_via_phrase(
                "*" + "_".join(prev_index_name.split("_")[1:]), ES_URL
            )

            new_index_name = st.selectbox(
                "new index name", target_index_list, placeholder="Select index name..."
            )
            # logger.info(f"selected new index: {new_index_name}")

        # 버튼을 누른 경우 실행
        if st.button(label="Change Aliases", type="primary", key="change_via_alias"):
            # 변경할 alias가 선택된 경우만 실행
            if alias_name and new_index_name:
                logger.info(
                    f"'{alias_name}' change from: {prev_index_name} -> to: {new_index_name}"
                )
                result, resp = change_aliases_old_to_new(
                    prev_index_name,
                    new_index_name,
                    [alias_name],
                    ES_URL,
                )

                st.text(result)
                st.json(resp.text)
            else:
                st.error("old index를 선택하여 변경할 alias를 정해주세요.")

with ui_tab_index:
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
