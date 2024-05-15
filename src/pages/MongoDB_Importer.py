import os
import pandas as pd
import streamlit as st
import pymongo as pm
from functools import wraps
import time
from datetime import timedelta
import logging
import json
from app.db_api import csv2mongo, store2csv, store2json, json2mongo, async_save_to_bson

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="MongoDB Importer",
)

# 경로 설정이 안된 경우 index페이지에서 진행
if "streamlit_path" not in st.session_state:
    st.switch_page("index.py")

# 사용 파일 경로
secrets_path = os.path.join(st.session_state.streamlit_path, "secrets.toml")
mongo_schema_path = os.path.join(st.session_state.resources_path, "mongo_schema.json")


# 파일 업로드 모달
@st.experimental_dialog("config file is not exist.")
def file_not_exist_dialog(path, _type: list[str]):
    st.code(f"{path}")
    st.write("is not exist")

    uploaded_file = st.file_uploader(
        label="Upload config file",
        type=_type,
        accept_multiple_files=False,
    )
    if uploaded_file is not None:
        logger.info(f"{path} file is uploaded")
        try:
            with open(path, "wb") as f:
                f.write(uploaded_file.getvalue())
        except Exception as e:
            # st.switch_page("pages/MongoDB_Importer.py")
            st.error(e)

    if st.button("confirm"):
        st.switch_page("pages/MongoDB_Importer.py")


# config 파일이 없는 경우 경고 모달로 파일 업로드
if not os.path.exists(secrets_path):
    logger.warning("secrets.toml file isn't exist")
    file_not_exist_dialog(secrets_path, ["toml"])
    st.stop()

if not os.path.exists(mongo_schema_path):
    logger.warning("mongo_schema.json file isn't exist")
    file_not_exist_dialog(mongo_schema_path, ["json"])
    st.stop()


def return_processing_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return timedelta(seconds=(end_time - start_time)), result

    return wrapper


# secrets 파일에서 정보가 있는지 체크 없으면 파일 업로드 로직 수행
try:
    _ = st.secrets["connections"]
    _ = st.secrets["mongo"]
except KeyError:
    logger.warning("secrets.toml file is wrong")
    st.error("secrets.toml file is wrong")
    file_not_exist_dialog()
    st.stop()
except FileNotFoundError:
    logger.warning("secrets.toml file isn't exist")
    st.error("secrets.toml file isn't exist")
    file_not_exist_dialog()
    st.stop()


# rdb_info 기본값 지정 및 수정 가능. (파일이 수정되지는 않음)
with st.expander(label="rdb info") as rdb_info:
    rdb_host = st.text_input("ip", value=st.secrets.connections.rdb.host)
    rdb_port = st.text_input("port", value=st.secrets.connections.rdb.port)
    rdb_database = st.text_input("database", value=st.secrets.connections.rdb.database)
    rdb_username = st.text_input("username", value=st.secrets.connections.rdb.username)
    rdb_password = st.text_input(
        "password", type="password", value=st.secrets.connections.rdb.password
    )

# mongodb_info 기본값 지정 및 수정 가능. (파일이 수정되지는 않음)
with st.expander(label="mongodb info") as mongodb_info:
    mongodb_host = st.text_input("mongodb host", value=st.secrets.mongo.host)
    mongodb_port = st.number_input("mongodb port", value=st.secrets.mongo.port)
    mongodb_username = st.text_input(
        "mongodb username", value=st.secrets.mongo.username
    )
    mongodb_password = st.text_input(
        "mongodb password", type="password", value=st.secrets.mongo.password
    )


@st.cache_resource
def init_connection():
    return pm.MongoClient(
        host=mongodb_host,
        port=mongodb_port,
        username=mongodb_username,
        password=mongodb_password,
    )


mongo_client = init_connection()


@return_processing_time
def get_data_from_rdb(conn, query) -> pd.DataFrame:
    df = conn.query(query, ttl=60 * 30)
    st.dataframe(df.head(5))
    return df


st.divider()

# if st.button("Load MongoDB Schema File", type="primary"):
with open(mongo_schema_path, "r", encoding="utf-8") as f:
    mongo_schema = json.load(f)
    tasks = mongo_schema.keys()
    selected_collection = st.selectbox("select task", tasks)

task = mongo_schema[selected_collection]


db_list = [
    item
    for item in mongo_client.list_database_names()
    if item not in ["admin", "config", "local"]
]

mongo_db_name = st.selectbox("Database", db_list)

# st.text_input(
#     "mongo db name",
#     placeholder="Enter DB name...",
# )
rdb_query = st.text_area(
    "rdb query", placeholder="select * from table", value=task["query"]
)
mongo_collection_name = st.text_input(
    "mongo collection name",
    placeholder="Enter collection name...",
    value=task["collection"],
)

st.divider()
conn = st.connection(
    "rdb",
    type="sql",
    url=f"mariadb://{rdb_username}:{rdb_password}@{rdb_host}:{rdb_port}/{rdb_database}",
)
# df = conn.query("select CRHID, CRH, LANG from tbl_names_ml_crh limit 1000", ttl=600)
# st.dataframe(df)


# @return_processing_time
# def insert2mongodb(db_name, collection_name, dataframe: pd.DataFrame):
#     # db = mongo_client.get_database(db_name)
#     # collection = db.create_collection(collection_name)
#     collection.insert_many(dataframe.to_dict(orient="records"))


@return_processing_time
def store2json_w_time(df):
    return store2json(df)


@return_processing_time
def json2mongo_w_time(path, db, user, pw, host, port, task):
    return json2mongo(
        path=path, db=db, user=user, pw=pw, host=host, port=port, task=task
    )


@return_processing_time
def store2csv_w_time(df):
    return store2csv(df)


@return_processing_time
def csv2mongo_w_time(path, columns, db, user, pw, host, port, task):
    return csv2mongo(
        path=path,
        columns=columns,
        db=db,
        user=user,
        pw=pw,
        host=host,
        port=port,
        task=task,
    )


if st.button("migrate to mongo"):
    if "" in [rdb_query, mongo_db_name, mongo_collection_name]:
        st.warning(
            "please enter ['rdb query', 'mongo db name', 'mongo collection name']"
        )
    else:

        with st.status(
            f"Migrate to mongodb.{mongo_db_name}.{mongo_collection_name} ...",
            expanded=True,
        ) as status:
            st.write("Fetching from RDB...")
            processing_time1, data = get_data_from_rdb(conn, rdb_query)
            st.write(f"Fetching complete({processing_time1}).")

            st.write(f"Storing to temp file...")
            # processing_time2, path = store2json_w_time(data)
            processing_time2, path = store2csv_w_time(data)
            st.write(f"Storing complete({processing_time2}).")

            # st.write("Fetching RDB and Saving to bson...")
            # processing_time1, path = async_save_to_bson(
            #     {
            #         "host": rdb_host,
            #         "user": rdb_username,
            #         "password": rdb_password,
            #         "db": rdb_database,
            #     },
            #     rdb_query,
            # )
            # st.write(f"Fetching & Saving complete({processing_time1}).")

            st.write("Importing into mongodb...")
            # processing_time3, reuslt = json2mongo_w_time(
            #     path,
            #     db=mongo_db_name,
            #     user=mongodb_username,
            #     pw=mongodb_password,
            #     host=mongodb_host,
            #     port=mongodb_port,
            #     task=task,
            # )
            processing_time3, reuslt = csv2mongo_w_time(
                path,
                columns=data.columns,
                db=mongo_db_name,
                user=mongodb_username,
                pw=mongodb_password,
                host=mongodb_host,
                port=mongodb_port,
                task=task,
            )
            st.write(f"Importing complete({processing_time3}).")

            # st.write("Inserting into MongoDB")
            # # processing_time2, _ = insert2mongodb(
            # #     mongo_db_name, mongo_collection_name, data
            # # )
            # st.write(f"Inserting complete({processing_time2})")

            status.update(
                label=f"Migrating complete! total time: {sum([processing_time1,processing_time2,processing_time3], timedelta())}",
                state="complete",
            )
