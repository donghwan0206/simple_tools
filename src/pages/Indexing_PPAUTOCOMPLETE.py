import json
import os
import time
import streamlit as st
import pandas as pd
from app.es_api import indexing_ppautocomplete

st.set_page_config(
    layout="wide",
    page_title="Indexing PPAUTOCOMPLETE",
)


if "resources_path" not in st.session_state:
    st.switch_page("index.py")

config_path = os.path.join(st.session_state.resources_path, "conf2.json")


@st.experimental_dialog("config file is not exist.")
def dialog():
    st.code(f"{config_path}")
    st.write("is not exist")

    if st.button("confirm"):
        st.switch_page("index.py")


if not os.path.exists(config_path):
    dialog()

else:
    with open(config_path, mode="r") as f:
        config = json.load(f)

    index_list = list(config["index"].keys())[1:]
    locales = ["KR", "US", "EP", "CN", "JP"]

    indexing_tab, editor_tab = st.tabs(["Indexing", "Edit query"])

    with indexing_tab:
        version = st.text_input("version number", placeholder="9999")
        locale = st.selectbox("locale", locales, key="locale").lower()
        data_df = pd.DataFrame(
            [(a, True) for a in index_list], columns=["index", "select"]
        )
        stdf = st.data_editor(
            data_df,
            column_config={
                "select": st.column_config.CheckboxColumn("select", default=True)
            },
            # disabled=["alias"],
            hide_index=True,
        )

        if st.button("Start Indexing", type="primary"):
            select_df = stdf[stdf["select"]]
            if len(select_df) > 0 and version != "":
                progress_cnt = 100 % len(select_df)
                progress_bar = st.progress(progress_cnt, text="indexing")
                for _, row in select_df.iterrows():
                    # time.sleep(1)
                    indexing_ppautocomplete(
                        version=version,
                        index=row["index"],
                        locale=locale,
                        conf=config_path,
                    )
                    progress_cnt += 100 // len(select_df)
                    progress_bar.progress(
                        progress_cnt, text=f"indexing... {row['index']}"
                    )
                progress_bar(100, text="indexing complete")
                st.write(select_df)
    with editor_tab:
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
            edited_query = st.text_area(
                "code edit",
                value=target_query,
                label_visibility="collapsed",
                height=600,
            )
            if st.button("save query", type="primary"):
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
