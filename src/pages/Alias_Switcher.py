import streamlit as st
import pandas as pd
import logging
from app.es_api import (
    get_aliases_via_index_name,
    change_aliases_old_to_new,
    get_all_indices,
    get_all_aliases,
    get_indices_wo_alias_except_dev,
    get_indices_via_phrase,
)

logger = logging.getLogger(__name__)

# 메인 페이지에서 elasticsearch url 셋팅 안하고 오면 메인 페이지로 redirect
if "ES_URL" not in st.session_state:
    st.switch_page("index.py")

st.set_page_config(
    layout="wide",
    page_title="Alias Switcher",
)

# ES URL 설정
ES_URL = st.session_state["ES_URL"]

selected_aliases = []

ui_tab_alias, ui_tab_index, ui_tab_multi = st.tabs(["via Alias", "via Index", "multi"])

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


def reload_index_list():
    if "data_df" in st.session_state:
        st.session_state.pop("data_df")
    status, indices = get_indices_wo_alias_except_dev(ES_URL)
    if status:
        st.session_state.data_df = pd.DataFrame(
            [(a, False) for a in indices], columns=["index", "select"]
        )
    else:
        st.error("Fail")


with ui_tab_multi:
    # TODO
    # 1. alias 지정안된 인덱스 리스트 보여주기
    # 2. 해당 리스트와 인덱스명이 유사하며 alias
    ui_col_left, ui_col_right = st.columns(2)
    index_list = []

    if "data_df" not in st.session_state:
        reload_index_list()

    with ui_col_left:
        st.subheader("List of index(with no alias)")
        if st.button("Reload list of index", type="primary"):
            reload_index_list()

    ui_col_left_search, ui_col_right_btn1, ui_col_right_btn2 = st.columns([4, 1, 1])

    with ui_col_left_search:
        search_words = st.text_input(label="search", placeholder="e.g. locale")
        search_words = search_words.strip().split(" ")
        search_df = st.session_state.data_df

        for word in search_words:
            search_df = search_df[search_df["index"].str.contains(word, na=False)]
        # st.code(search_words)

    with ui_col_right_btn2:
        st.session_state.dev_only = st.checkbox("dev only")
        # 버튼을 누른 경우 실행
        if st.button(label="Change All Aliases", type="primary"):
            # 변경할 alias가 선택된 경우만 실행
            if len(st.session_state.df_list) > 0:
                for new_index, prev_index, aliases in st.session_state.df_list:
                    logger.info(
                        f"{aliases} change - from: {prev_index} ->  to: {new_index}"
                    )
                    result, resp = change_aliases_old_to_new(
                        prev_index,
                        new_index,
                        aliases,
                        ES_URL,
                    )

                    st.text(result)
                    st.json(resp.text)
            else:
                st.error("검색을 통해 선택하여 변경할 index를 정해주세요.")

    if search_words != [""]:
        st.session_state.df_list = []
        for i, row in search_df.iterrows():
            st.divider()
            ui_col_left_2, ui_col_right_1, ui_col_right_2 = st.columns([1, 1, 1])
            with ui_col_left_2:
                st.selectbox("index", [row["index"]], disabled=True)

            with ui_col_right_1:

                _, target_index_list = get_indices_via_phrase(
                    "*" + "_".join(row["index"].split("_")[1:]), ES_URL
                )
                target_index_list.remove(row["index"])
                target_index_list.insert(0, None)
                change_index_name = st.selectbox(
                    f"change for {row['index']}",
                    target_index_list,
                    placeholder="Select index name...",
                )

            with ui_col_right_2:
                if change_index_name is not None:
                    result, resp = get_aliases_via_index_name(
                        index_name=change_index_name, es_url=ES_URL
                    )

                    # 성공적으로 alias를 받았을 경우(alias가 0 건인 경우도 포함)
                    if result:
                        if st.session_state.dev_only:
                            for e in resp.copy():
                                if "dev" not in e:
                                    resp.remove(e)

                        st.text("alias")
                        st.table(resp)

            if change_index_name is not None:
                st.session_state.df_list.append([row["index"], change_index_name, resp])
    else:
        st.session_state.df_list = []
        st.table(search_df["index"])
    # st.code(st.session_state.df_list)
