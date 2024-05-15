import asyncio
import aiomysql
import aiofiles
import bson.json_util
import pandas as pd
import bson
import json
import os
import logging
import subprocess

logger = logging.getLogger(__name__)

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(FILE_DIR, "../../")

LOG_DIR = os.path.join(BASE_DIR, "logs")
TEMP_DIR = os.path.join(BASE_DIR, "temp")


def json2mongo(path, db, user, pw, host, port, task):
    mongoimport_command = [
        "mongoimport",
        "--uri",
        f"mongodb://{user}:{pw}@{host}:{port}",
        "--authenticationDatabase",
        '"admin"',
        "--db",
        f"{db}",
        "--collection",
        f"{task['collection']}",
        "--file",
        f"{path}",
        "--jsonArray",
        "--numInsertionWorkers",
        "4",
    ]
    logger.info(mongoimport_command)
    logger.info(f"mongoimport start")
    result = subprocess.run(mongoimport_command, capture_output=True, text=True)
    logger.info(f"subprocess stdout: {result.stdout}")
    logger.info(f"subprocess stderr: {result.stderr}")

    if result.returncode == 0:
        logger.info("Data imported successfully")
        return 0
    else:
        logger.error("Error occurred during import")
        return 1


async def fetch_batch(cursor, query, batch_size):
    """배치 단위로 데이터를 읽어오는 비동기 함수"""
    await cursor.execute(query)
    while True:
        rows = await cursor.fetchmany(batch_size)
        if not rows:
            break
        df = pd.DataFrame(
            rows,
            columns=[desc[0] for desc in cursor.description],
            dtype="string[pyarrow]",
        )
        yield df


async def save_to_bson(filename, df):
    """데이터프레임을 BSON 파일로 비동기 저장"""
    df_dict = df.to_dict("records")
    async with aiofiles.open(filename, "ab") as file:
        for record in df_dict:
            await file.write(bson.encode(record))


async def fetch_and_save_batches(db_config, query, batch_size, output_file):
    """데이터를 비동기 배치 단위로 읽고 BSON 파일로 저장"""
    conn = await aiomysql.connect(**db_config)
    try:
        async with conn.cursor() as cursor:
            async for df in fetch_batch(cursor, query, batch_size):
                await save_to_bson(output_file, df)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()


def async_save_to_bson(db_config, query, batch_size=10000):
    """비동기적으로 데이터를 저장하는 메인 함수"""
    # 기존 파일이 있으면 삭제
    import os

    temp_path = os.path.join(TEMP_DIR, "temp.bson")

    if os.path.exists(temp_path):
        os.remove(temp_path)

    # 이벤트 루프 생성 및 실행
    asyncio.run(fetch_and_save_batches(db_config, query, batch_size, temp_path))

    return temp_path


def store2json(df: pd.DataFrame):
    # logger.info("convert data type")
    # df = df.astype("string[pyarrow]")
    # logger.info("complete convert data type")
    logger.info("convert to dict")
    df_dict = df.to_dict(orient="records")
    logger.info(type(df_dict))
    logger.info("complete convert to dict")
    temp_path = os.path.join(TEMP_DIR, "temp.json")

    try:
        with open(temp_path, "w") as f:
            json.dump(df_dict, f)
        logger.info("Complete: DataFrame to bson file ")
        return temp_path
    except Exception as e:
        logger.warning("Fail: DataFrame to bson file")
        logger.error(e)
        return None


def store2csv(df: pd.DataFrame):
    # logger.info("convert data type")
    # df = df.astype("string[pyarrow]")
    # logger.info("complete convert data type")
    # logger.info("convert to dict")
    # df_dict = df.to_dict(orient="records")
    # logger.info(type(df_dict))
    # logger.info("complete convert to dict")
    temp_path = os.path.join(TEMP_DIR, "temp.csv")

    try:
        # with open(temp_path, "w") as f:
        #     json.dump(df_dict, f)
        df.to_csv(temp_path, index=False)
        logger.info("Complete: DataFrame to temp file ")
        return temp_path
    except Exception as e:
        logger.warning("Fail: DataFrame to temp file")
        logger.error(e)
        return None


def csv2mongo(path, schema, db, user, pw, host, port, task):
    mongoimport_command = [
        "mongoimport",
        "--uri",
        f"mongodb://{user}:{pw}@{host}:{port}",
        "--authenticationDatabase",
        '"admin"',
        "--db",
        f"{db}",
        "--collection",
        f"{task['collection']}",
        "--type",
        "csv",
        "--columnsHaveTypes",
        "--fields",
        ",".join([f"{k}.{v}()" for k, v in schema.items()]),
        "--headerline" "--file",
        f"{path}",
        "--numInsertionWorkers",
        "4",
    ]
    logger.info(mongoimport_command)
    logger.info(f"mongoimport start")
    result = subprocess.run(mongoimport_command, capture_output=True, text=True)
    logger.info(f"subprocess stdout: {result.stdout}")
    logger.info(f"subprocess stderr: {result.stderr}")

    if result.returncode == 0:
        logger.info("Data imported successfully")
        return 0
    else:
        logger.error("Error occurred during import")
        return 1
