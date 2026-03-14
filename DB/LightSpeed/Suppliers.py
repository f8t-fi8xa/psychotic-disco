from . import _Pipe as Pipe
import json

supplier_request = Pipe.Request("suppliers")

path = r"C:\Users\liams\Gallery\DB\resources\Deals.json"
with open(path, 'r') as file:
    deals = json.load(file)

class Suppliers:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()

    def _extract_attributes(self, supplier):
        self.cur.execute("SELECT supplier_code FROM products WHERE supplier_id = %s LIMIT 1", supplier['id'])
        c = self.cur.fetchone()
        if not c:
            return None
        code = c[0]
        if code in deals:
            seller_type = deals[code]["seller_type"], 
            tier = deals[code]["tier"],
            deal_type = deals[code]["deal_type"],
            deal = deals[code]["deal"]
        else:
            seller_type = None, 
            tier = None,
            deal_type = None,
            deal = None

        attrs = {
            "id": supplier["id"],
            "name": supplier["name"],
            "code": code,
            "active": supplier["name"][0] != 'z',
            "seller_type": seller_type,
            "tier": tier,
            "deal_type": deal_type,
            "deal": deal
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