from . import _Pipe as Pipe
import json
import sqlite3

supplier_request = Pipe.Request("suppliers")

path = r"C:\Users\liams\Gallery\DB\resources\Deals.json"
with open(path, 'r') as file:
    deals = json.load(file)

class Suppliers:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()

    def _extract_attributes(self, supplier):
        self.cur.execute(f"SELECT supplier_code FROM products WHERE supplier_id = '{supplier['id']}' LIMIT 1")
        code = self.cur.fetchone()
        if not code:
            return None
        d = {} if code[0] not in deals else deals[code[0]]

        if d.get("tags"):
            d.pop("tags")

        attrs = {
            "id": supplier["id"],
            "name": supplier["name"],
            "code": code[0],
            "active": supplier["name"][0] != 'z'
        }
        return attrs | d

    def update(self):
        print("Updating suppliers...")
        self.cur.execute("DELETE FROM suppliers")
        self.conn.commit()

        last_version = 0
        batch = supplier_request.get(after=last_version)

        while len(batch) > 0:
            for supplier in batch:
                attrs = self._extract_attributes(supplier)
                Pipe.put_sql(self.conn, attrs, "suppliers")

                last_version = supplier["version"]
            batch = supplier_request.get(after=last_version)