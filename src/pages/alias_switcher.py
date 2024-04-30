import streamlit as st
import pandas as pd
from app.es_api import (
    get_aliases_via_index_name,
    change_aliases_old_to_new,
    get_indices,
)

if "ES_URL" not in st.session_state:
    st.switch_page("index.py")

ES_URL = st.session_state["ES_URL"]

col1, col2 = st.columns(2)

status, index_list = get_indices(ES_URL)

with col1:
    # old_index_name = st.text_input("old index name")
    old_index_name = st.selectbox(
        "old index name",
        index_list,
        index=None,
        placeholder="Select index name...",
    )
    st.write("Old Index:", old_index_name)

    if old_index_name is not None:
        result, resp = get_aliases_via_index_name(
            index_name=old_index_name, es_url=ES_URL
        )
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
            if len(stdf) > 0:
                selected_aliases = stdf[stdf["select"]]["alias"]
                st.header("selected aliases")
                st.dataframe(selected_aliases, hide_index=True)
        else:
            st.json(resp)

with col2:
    # new_index_name = st.text_input("new index name")
    new_index_name = st.selectbox(
        "new index name",
        index_list,
        index=None,
        placeholder="Select index name...",
    )
    st.write("New Index:", new_index_name)

    if st.button(label="Change Aliases", type="primary"):
        result, resp = change_aliases_old_to_new(
            old_index_name,
            new_index_name,
            selected_aliases,
            ES_URL,
        )

        st.text(result)
        st.json(resp.text)
