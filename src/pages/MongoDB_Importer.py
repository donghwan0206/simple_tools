import pandas as pd
import streamlit as st
import pymongo as pm
from functools import wraps
import time
from datetime import timedelta


def return_processing_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return timedelta(seconds=(end_time - start_time)), result

    return wrapper


with st.expander(label="rdb info") as rdb_info:
    rdb_host = st.text_input("ip", value=st.secrets.connections.rdb.host)
    rdb_port = st.text_input("port", value=st.secrets.connections.rdb.port)
    rdb_database = st.text_input("database", value=st.secrets.connections.rdb.database)
    rdb_username = st.text_input("username", value=st.secrets.connections.rdb.username)
    rdb_password = st.text_input(
        "password", type="password", value=st.secrets.connections.rdb.password
    )

with st.expander(label="mongodb info") as mongodb_info:
    mongodb_host = st.text_input("mongodb host", value=st.secrets.mongo.host)
    mongodb_port = st.number_input("mongodb port", value=st.secrets.mongo.port)
    mongodb_username = st.text_input(
        "mongodb username", value=st.secrets.mongo.username
    )
    mongodb_password = st.text_input(
        "mongodb password", type="password", value=st.secrets.mongo.password
    )

st.divider()
rdb_query = st.text_area("rdb query", placeholder="select * from table")
mongo_db_name = st.text_input("mongo db name", placeholder="Enter DB name...")
mongo_collection_name = st.text_input(
    "mongo collection name", placeholder="Enter collection name..."
)

st.divider()
conn = st.connection(
    "rdb",
    type="sql",
    url=f"mariadb://{rdb_username}:{rdb_password}@{rdb_host}:{rdb_port}/{rdb_database}",
)
# df = conn.query("select CRHID, CRH, LANG from tbl_names_ml_crh limit 1000", ttl=600)
# st.dataframe(df)


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
def get_data_from_rdb(conn, query):
    df = conn.query(query, ttl=60 * 30)
    st.dataframe(df.head(5))
    return df


# items = get_data()

# st.dataframe(items)


@return_processing_time
def insert2mongodb(db_name, collection_name, dataframe: pd.DataFrame):
    db = mongo_client.get_database(db_name)
    collection = db.create_collection(collection_name)
    collection.insert_many(dataframe.to_dict(orient="records"))


if st.button("migrate to mongo"):
    if "" in [rdb_query, mongo_db_name, mongo_collection_name]:
        st.warning(
            "please enter ['rdb query', 'mongo db name', 'mongo collection name']"
        )
    else:
        # st.write(rdb_query)
        # st.write(mongo_db_name)
        # st.write(mongo_collection_name)
        with st.status(
            f"Migrate to mongodb.{mongo_db_name}.{mongo_collection_name} ...",
            expanded=True,
        ) as status:
            st.write("Fetching from RDB...")
            processing_time1, data = get_data_from_rdb(conn, rdb_query)
            st.write(f"Fetching complete({processing_time1}).")
            st.write("Inserting into MongoDB")
            processing_time2, _ = insert2mongodb(
                mongo_db_name, mongo_collection_name, data
            )
            st.write(f"Inserting complete({processing_time2})")

            status.update(
                label=f"Migrating complete! total time: {processing_time1+processing_time2}",
                state="complete",
            )
