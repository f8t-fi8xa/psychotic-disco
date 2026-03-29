from . import _Pipe as Pipe
import json
import os

supplier_request = Pipe.Request("suppliers")

with open(os.path.join('resources', 'Deals.json'), 'r') as file:
    deals = json.load(file)

class Suppliers:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()

    def _extract_attributes(self, supplier):
        attrs = {
            "id": supplier["id"],
            "name": supplier["name"],
            "active": supplier["name"][0] != 'z',
        }
        return attrs

    def update(self):
        print("Updating suppliers...")

        last_version = 0
        batch = supplier_request.get(after=last_version)

        while len(batch) > 0:
            for supplier in batch:
                attrs = self._extract_attributes(supplier)
                if attrs: 
                    Pipe.put_sql(self.conn, attrs, "suppliers")

                last_version = supplier["version"]
            batch = supplier_request.get(after=last_version)