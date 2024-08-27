import requests
from requests.exceptions import ConnectTimeout, Timeout
import asyncio
from .auto_indexing.src import indexing_service
from pandas import DataFrame


def check_es_url(url: str):
    if url == "":
        return False

    try:
        resp = requests.get(url, timeout=5)
    except ConnectTimeout as e:
        return False

    if resp.status_code == 200 and resp.json()["version"]["number"].startswith("7"):
        return True
    else:
        return False


def get_indices_wo_alias(
    es_url: str,
) -> tuple[bool, list] | tuple[bool, requests.Response]:
    end_point = f"{es_url}/_alias"

    resp = requests.get(end_point)

    if resp.status_code == 200:
        index_list = []
        for k, v in resp.json().items():
            if len(v["aliases"]) > 0:
                continue
            elif not k.startswith("."):
                index_list.append(k)
            index_list.sort()
        return True, index_list
    else:
        return False, resp


def get_indices_wo_alias_except_dev(
    es_url: str,
) -> tuple[bool, list] | tuple[bool, requests.Response]:
    end_point = f"{es_url}/_alias"

    resp = requests.get(end_point)

    if resp.status_code == 200:
        index_list = []
        for k, v in resp.json().items():
            if len(v["aliases"]) == 1 and "hsdev" in v["aliases"][0]:
                index_list.append(k)
            elif len(v["aliases"]) > 0:
                continue
            elif not k.startswith("."):
                index_list.append(k)
            index_list.sort()
        return True, index_list
    else:
        return False, resp


def delete_indices(indices: list, es_url: str):
    fail_list = []

    for index in indices:
        end_point = f"{es_url}/{index}"
        resp = requests.delete(end_point)

        if resp.status_code == 200 and resp.json()["acknowledged"] == True:
            continue
        else:
            fail_list.append(resp.json())
    if len(fail_list) == 0:
        return True, fail_list
    else:
        return False, fail_list


def get_aliases_via_index_name(index_name: str, es_url: str) -> tuple[bool, dict]:
    """
    index를 입력받아 해당 index에 할당된 alias를 반환

    Args:
        index_name (str): _description_
        es_url (str): _description_

    Returns:
        tuple[bool, dict]: _description_
    """
    end_point = f"{es_url}/{index_name}/_alias"

    resp = requests.get(end_point)

    # resp = resp.json()

    if resp.status_code == 200:
        return True, list(resp.json()[index_name]["aliases"].keys())
    else:
        return False, resp["error"]


def get_all_aliases(es_url: str) -> tuple[bool, dict]:
    import pandas as pd

    end_point = f"{es_url}/_cat/aliases?format=json&s=index:desc"

    resp = requests.get(end_point)

    if resp.status_code == 200:
        return True, {
            alias: group["index"].to_list()
            for alias, group in pd.DataFrame(resp.json()).groupby("alias")
            if not alias.startswith(".")
        }
    else:
        return False, resp


def get_indices_via_phrase(phrase: str, es_url: str) -> tuple[bool, DataFrame]:
    """_summary_

    Args:
        phrase (str): _description_
        es_url (str): _description_

    Returns:
        tuple[bool, dict]: _description_
    """
    import pandas as pd

    end_point = f"{es_url}/_cat/indices/{phrase}?format=json&s=index:desc"

    resp = requests.get(end_point)

    if resp.status_code == 200:
        return True, pd.DataFrame(resp.json())["index"].to_list()
    else:
        return False, resp


def get_all_indices(
    es_url: str,
) -> tuple[bool, DataFrame] | tuple[bool, requests.Response]:
    import pandas as pd

    end_point = f"{es_url}/_cat/indices?format=json&s=index:desc"

    resp = requests.get(end_point)

    if resp.status_code == 200:
        return True, pd.DataFrame(resp.json())["index"].to_list()
    else:
        return False, resp


def change_aliases_old_to_new(old_index, new_index, aliases, es_url):
    end_point = f"{es_url}/_aliases"
    headers = {"Content-Type": "application/json; charset=utf-8"}

    actions = []

    for alias in aliases:
        actions.append(
            {
                "remove": {
                    "index": f"{old_index}",
                    "alias": f"{alias}",
                }
            }
        )
        actions.append(
            {
                "add": {
                    "index": f"{new_index}",
                    "alias": f"{alias}",
                }
            }
        )

    param = {"actions": actions}

    resp = requests.post(end_point, json=param, headers=headers)

    if resp.status_code == 200:
        return True, resp
    else:
        return False, resp


def indexing_ppautocomplete(version, index, locale, conf):
    status, message = asyncio.run(indexing_service(version, index, locale, conf))

    if status == 1:
        return True
    else:
        return False
