import os
import pandas as pd
import streamlit as st
import pymongo as pm
from functools import wraps
import time
from datetime import timedelta, datetime
import logging
import json
from app.db_api import csv2mongo, store2csv, store2json, json2mongo

logger = logging.getLogger(__name__)

st.set_page_config(
    layout="wide",
    page_title="MongoDB Importer",
)


if "file_list" not in st.session_state:
    st.session_state.file_list = []

# 경로 설정이 안된 경우 index페이지에서 진행
if "streamlit_path" not in st.session_state:
    st.switch_page("index.py")

# 사용 파일 경로
secrets_path = os.path.join(st.session_state.streamlit_path, "secrets.toml")
mongo_schema_path = os.path.join(st.session_state.resources_path, "mongo_schema.json")


if "mongo_schema" not in st.session_state:
    with open(mongo_schema_path, "r", encoding="utf-8") as f:
        mongo_schema = json.load(f)
        st.session_state.mongo_schema = mongo_schema


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


@st.experimental_dialog("config file is not exist.")
def upload_csv_data(file_name, _type: list[str] = ["csv"]):
    st.markdown(f"# uplooad for `{file_name}`")
    uploaded_file = st.file_uploader(
        label="Upload config file",
        type=_type,
        accept_multiple_files=False,
    )
    path = os.path.join(st.session_state.temp_path, f"{file_name}_{datetime.now()}.csv")
    if uploaded_file is not None:
        logger.info(f"{path} file is uploaded")
        try:
            with open(path, "wb") as f:
                f.write(uploaded_file.getvalue())
        except Exception as e:
            # st.switch_page("pages/MongoDB_Importer.py")
            st.error(e)

    if st.button("confirm"):
        st.session_state[file_name] = path
        st.rerun()
        return path
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


# # rdb_info 기본값 지정 및 수정 가능. (파일이 수정되지는 않음)
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


# 실행 시간 체크 데코레이터
def return_processing_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return timedelta(seconds=(end_time - start_time)), result

    return wrapper


@return_processing_time
def store2json_w_time(df):
    return store2json(df)


@return_processing_time
def json2mongo_w_time(path, db, user, pw, host, port, collection):
    return json2mongo(
        path=path,
        db=db,
        user=user,
        pw=pw,
        host=host,
        port=port,
        collection=collection,
    )


@return_processing_time
def store2csv_w_time(df, schema):
    return store2csv(df, schema)


@return_processing_time
def csv2mongo_w_time(path, schema, db, user, pw, host, port, collection):
    return csv2mongo(
        path=path,
        schema=schema,
        db=db,
        user=user,
        pw=pw,
        host=host,
        port=port,
        collection=collection,
    )


@return_processing_time
def create_index(collection, indexes):
    for index in indexes:
        collection.create_index(index)


# pymongo client 연결
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
def get_data_from_rdb(conn, query, show=False) -> pd.DataFrame:
    df = conn.query(query, ttl=60 * 30)
    if show:
        st.dataframe(df.head(5))
    return df


# mongodb 데이터베이스 선택
st.divider()
db_list = [
    item
    for item in mongo_client.list_database_names()
    if item not in ["admin", "config", "local"]
]
mongo_db_name = st.selectbox("Database", db_list)
st.divider()


# csv 파일로 입력받는 컬렉션 용
# 파일을 업로드한 후 업로드한 파일이름을 테이블 형태로 보여줌
with st.container():

    uploaded_file = st.file_uploader(
        label="Upload csv file",
        type=["csv"],
        accept_multiple_files=False,
    )

    if uploaded_file is not None:
        path = os.path.join(st.session_state.temp_path, f"{uploaded_file.name}")
        st.session_state.file_list.append(uploaded_file.name)
        try:
            with open(path, "wb") as f:
                f.write(uploaded_file.getvalue())
            logger.info(f"{path} file is uploaded")
            st.table(set(st.session_state.file_list))
        except Exception as e:
            # st.switch_page("pages/MongoDB_Importer.py")
            st.error(e)
st.divider()


@st.cache_data
def json2dataframe(json_data):
    return pd.DataFrame([x for x in json_data.values()])


# mongoschema 파일에서 기본정보 로딩
df = json2dataframe(st.session_state.mongo_schema)


# import정보 수정 테이블
edited_df = st.data_editor(
    df[
        [
            "import",
            "title",
            "collection",
            "data_source",
            "query",
            "rdb_host",
            "rdb_port",
            "rdb_db",
            "rdb_username",
            "rdb_password",
        ]
    ],
    column_config={
        "title": "title",
        "data_source": st.column_config.SelectboxColumn(
            "source",
            help="data source",
            width="small",
            options=["rdb", "csv"],
            required=True,
        ),
        "query": st.column_config.TextColumn(
            label="query (csv 파일의 경우 업로드후 파일명 작성)",
            required=True,
        ),
        "rdb_host": st.column_config.TextColumn(),
        "rdb_port": st.column_config.TextColumn(),
        "rdb_db": st.column_config.TextColumn(),
        "rdb_username": st.column_config.TextColumn(),
        "rdb_password": st.column_config.TextColumn(),
        "import": st.column_config.CheckboxColumn(),
        "conn_check": st.column_config.CheckboxColumn(),
        "schema": st.column_config.TextColumn(),
    },
    hide_index=True,
    height=600,
)


if st.button("RDB Connection Check"):
    rdb_df = edited_df[edited_df["data_source"] == "rdb"]
    rdb_df = rdb_df[rdb_df["import"]]
    # st.dataframe(rdb_df)
    for i, row in rdb_df.iterrows():
        if row["data_source"] == "rdb":
            collection = row["collection"]
            query = row["query"] + " limit 5"
            conn = st.connection(
                "rdb",
                type="sql",
                url=f"mariadb://{row['rdb_username']}:{row['rdb_password']}@{row['rdb_host']}:{row['rdb_port']}/{row['rdb_db']}",
            )
            _, data = get_data_from_rdb(conn, query=query)
            if len(data) > 0:
                # df[df["collection"] == collection]["conn_check"] = True
                df.iloc[i]["conn_check"] = True
                st.toast(f"✅ {collection}: DB connection is OK! ")
            else:
                st.warning(f"{collection}: DB connection is failed.")
            conn.close()


if st.button("Migrate to MongoDB", type="primary"):
    for col in edited_df.columns:
        df[col] = edited_df[col]
    selected_df = df[df["import"]]
    csv_df = selected_df[selected_df["data_source"] == "csv"]
    rdb_df = selected_df[selected_df["data_source"] == "rdb"]
    processing_time_list = []
    with st.status(
        f"Migrate to mongodb.{mongo_db_name} ...",
        expanded=True,
    ) as status:
        for i, row in csv_df.iterrows():
            mongo_collection_name = row["collection"]

            st.write("start: Importing into mongodb...")
            processing_time, reuslt = csv2mongo_w_time(
                os.path.join(st.session_state.temp_path, row["query"]),
                schema=row["schema"],
                db=mongo_db_name,
                user=mongodb_username,
                pw=mongodb_password,
                host=mongodb_host,
                port=mongodb_port,
                collection=mongo_collection_name,
            )
            processing_time_list.append(processing_time)
            st.write(f"Finish: Importing into mongodb... ({processing_time}).")

            st.write("Start: Create index")
            target_collection = mongo_client.get_database(mongo_db_name).get_collection(
                mongo_collection_name
            )
            processing_time, _ = create_index(target_collection, row["index"])
            processing_time_list.append(processing_time)
            st.write("Finish: Create index")

        for i, row in rdb_df.iterrows():
            conn = st.connection(
                "rdb",
                type="sql",
                url=f"mariadb://{row['rdb_username']}:{row['rdb_password']}@{row['rdb_host']}:{row['rdb_port']}/{row['rdb_db']}",
            )
            mongo_collection_name = row["collection"]
            st.write("Start: Fetching from RDB...")
            processing_time, data = get_data_from_rdb(conn, row["query"])
            st.write(f"Finish: Fetching from RDB... ({processing_time}).")
            processing_time_list.append(processing_time)
            st.write(f"Start: Storing to temp file...")
            processing_time, path = store2csv_w_time(data, row["schema"])
            st.write(f"Finish: Storing to temp file(path)... ({processing_time}).")
            processing_time_list.append(processing_time)
            st.write(f"Start: Importing into mongodb.{row['collection']}...")
            processing_time, reuslt = csv2mongo_w_time(
                path,
                schema=row["schema"],
                db=mongo_db_name,
                user=mongodb_username,
                pw=mongodb_password,
                host=mongodb_host,
                port=mongodb_port,
                collection=mongo_collection_name,
            )
            st.write(f"Finish: Importing into mongodb... ({processing_time}).")
            processing_time_list.append(processing_time)
            st.write("Start: Create index")
            target_collection = mongo_client.get_database(mongo_db_name).get_collection(
                mongo_collection_name
            )
            processing_time, _ = create_index(target_collection, row["index"])
            processing_time_list.append(processing_time)
            st.write("Finish: Create index")

        status.update(
            label=f"Migrating for csv complete  total time: {sum(processing_time_list, timedelta())}",
            state="complete",
        )
