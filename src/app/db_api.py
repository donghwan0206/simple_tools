import pandas as pd
import json
import os
import logging
import subprocess

logger = logging.getLogger(__name__)

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(FILE_DIR, "../../")

LOG_DIR = os.path.join(BASE_DIR, "logs")
TEMP_DIR = os.path.join(BASE_DIR, "temp")


def json2mongo(path, db, user, pw, host, port, collection):
    mongoimport_command = [
        "mongoimport",
        "--uri",
        f"mongodb://{user}:{pw}@{host}:{port}",
        "--authenticationDatabase",
        '"admin"',
        "--db",
        f"{db}",
        "--collection",
        f"{collection}",
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

    temp_path = os.path.join(TEMP_DIR, "temp.csv")

    try:
        df.to_csv(temp_path, index=False)
        logger.info("Complete: DataFrame to temp file ")
        return temp_path
    except Exception as e:
        logger.warning("Fail: DataFrame to temp file")
        logger.error(e)
        return None


def csv2mongo(path, schema, db, user, pw, host, port, collection):
    mongoimport_command = [
        "mongoimport",
        "--uri",
        f"mongodb://{user}:{pw}@{host}:{port}",
        "--authenticationDatabase",
        '"admin"',
        "--db",
        f"{db}",
        "--collection",
        f"{collection}",
        "--type",
        "csv",
        "--columnsHaveTypes",
        "--fields",
        ",".join([f"{k}.{v}()" for k, v in schema.items()]),
        "--headerline",
        "--file",
        f"{path}",
        "--numInsertionWorkers",
        "4",
    ]
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
