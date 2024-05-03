import streamlit as st
import pandas as pd
from app.es_api import (
    get_aliases_via_index_name,
    change_aliases_old_to_new,
    get_indices,
)

# 메인 페이지에서 elasticsearch url 셋팅 안하고 오면 메인 페이지로 redirect
if "ES_URL" not in st.session_state:
    st.switch_page("index.py")

# ES URL 설정
ES_URL = st.session_state["ES_URL"]

# Elastic cluster에서 index list 받아오기
status, index_list = get_indices(ES_URL)

ui_col_left, ui_col_right = st.columns(2)

selected_aliases = []

# 좌측 컬럼 UI
with ui_col_left:

    old_index_name = st.selectbox(
        "old index name",
        index_list,
        index=None,
        placeholder="Select index name...",
    )

    st.write("Old Index:", old_index_name)

    # old_index 선택했을 때만 출력
    if old_index_name is not None:
        result, resp = get_aliases_via_index_name(
            index_name=old_index_name, es_url=ES_URL
        )

        # 성공적으로 alias를 받았을 경우(alias가 0 건인 경우도 포함)
        if result:
            data_df = pd.DataFrame(
                [(a, True) for a in resp], columns=["alias", "select"]
            )
            stdf = st.data_editor(
                data_df,
                column_config={
                    "select": st.column_config.CheckboxColumn("select", default=True)
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
        "new index name",
        index_list,
        index=None,
        placeholder="Select index name...",
    )
    st.write("New Index:", new_index_name)

    # 버튼을 누른 경우 실행
    if st.button(label="Change Aliases", type="primary"):
        # 변경할 alias가 선택된 경우만 실행
        if selected_aliases:
            result, resp = change_aliases_old_to_new(
                old_index_name,
                new_index_name,
                selected_aliases,
                ES_URL,
            )

            st.text(result)
            st.json(resp.text)
        else:
            st.error("old index를 선택하여 변경할 alias를 정해주세요.")
