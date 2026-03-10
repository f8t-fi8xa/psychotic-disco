import json
import sqlite3
import requests
import traceback
from datetime import datetime

path = r"C:\Users\liams\Gallery\DB\resources\Info.json"
with open(path, 'r') as info:
    meta_data = json.load(info)

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {meta_data['token']}"
}
# Basic API calls
BASE_URL = meta_data["base_url"]


class Request():
    def __init__(self, scope, page_size=1000):
        self.scope = scope
        self.page_size = page_size

    def get(self, version: float = 2.0, page="", after=0, **kwargs):

        args = [f"after={after}", f"page_size={self.page_size}"] + [f"{key}={value}" for key, value in kwargs.items()]
        args_formatted = "&".join(args)

        request = requests.get(f"{BASE_URL}/{version}/{self.scope}/{page}?{args_formatted}", headers=headers).json()
        if "data" in request.keys():
            return request["data"]
        else:
            return request

    def put(call, payload, version="2.0"):
        args = ""
        return requests.put(f"{BASE_URL}/{version}/{call}{args}", headers=headers, json=payload)

    def post(call, payload, version="2.0"):
        args = ""
        return requests.post(f"{BASE_URL}/{version}/{call}{args}", headers=headers, json=payload)


def insert_placeholder(number: int):
    return f"({', '.join(['?'] * number)})"


def update_placeholder(values: list):
    iterable = [f"{v} = ?" for v in values]
    return ','.join(iterable)


def seconds(iso_str: str):
    try:
        return datetime.fromisoformat(iso_str).timestamp()
    except TypeError:
        return None


CUTOFF_DATE = seconds("2020-01-01T00:00:00+00:00")


def format(s: str):
    if len(s) == 0:
        return None
    elif s[-1] == "/":
        return s[:-1]
    else:
        return s


# SQL methods


def put_sql(conn, attrs: dict, table: str):
    cur = conn.cursor()
    if attrs is None:
        return

    keys = list(attrs.keys())
    values = list(attrs.values())

    try:
        cur.execute(
            f'''
            INSERT INTO {table}({",".join(keys)}) VALUES {insert_placeholder(len(keys))} 
            ON CONFLICT DO UPDATE SET {update_placeholder(values=keys)}''',
            values * 2
        )
        conn.commit()
    except sqlite3.InterfaceError as e:
        print({k: type(attrs[k]) for k in keys})
        traceback.print_exc()


def put_sql_many(conn, attrs: list, table: str):
    cur = conn.cursor()
    if attrs is None or len(attrs) == 0:
        return

    keys = list(attrs[0].keys())

    double_values = [list(a.values()) * 2 for a in attrs]

    cur.executemany(
        f'''
        INSERT INTO {table}({",".join(keys)}) VALUES {insert_placeholder(number=len(keys))} 
        ON CONFLICT DO UPDATE SET {update_placeholder(values=keys)}''',
        double_values
    )
    conn.commit()
