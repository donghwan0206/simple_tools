import requests


def get_aliases_via_index_name(index_name, es_url):
    end_point = f"{es_url}/{index_name}/_alias"

    resp = requests.get(end_point)

    # resp = resp.json()

    if resp.status_code == 200:
        return True, list(resp.json()[index_name]["aliases"].keys())
    else:
        return False, resp["error"]


def get_all_aliases(es_url):
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


def get_indices_via_phrase(phrase, es_url):
    import pandas as pd

    end_point = f"{es_url}/_cat/indices/{phrase}?format=json&s=index:desc"

    resp = requests.get(end_point)

    if resp.status_code == 200:
        return True, pd.DataFrame(resp.json())["index"].to_list()
    else:
        return False, resp


def get_all_indices(es_url):
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
