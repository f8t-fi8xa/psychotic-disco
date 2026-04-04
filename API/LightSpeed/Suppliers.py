from . import _Pipe as Pipe

supplier_request = Pipe.Request("suppliers")

class Suppliers:
    def __init__(self, conn, cur=None):
        self.conn = conn
        self.cur = conn.cursor() if cur is None else cur

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