from . import _Pipe as Pipe

order_request = Pipe.Request("consignments")

class Orders:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()

    def _extract_attributes(self, order):
        attrs = {
            "id": order['id'],
            "supplier_id": order['supplier_id'],
            "name": order['name'],
            "reference": order['reference'],
            "type": order['type'],
            "date": Pipe.seconds(order['consignment_date']),
            "received_at": Pipe.seconds(order['received_at']),
            "status": order['status'],
            "version": order['version']
        }
        return attrs

    def update(self, append=True):
        print("Updating orders...")
        
        self.cur.execute("SELECT cutoff FROM config LIMIT 1")
        c = self.cur.fetchall()
        cutoff = int(c[0]) if c else 0

        if append:
            self.cur.execute("SELECT version FROM orders ORDER BY version DESC LIMIT 1")
            v = self.cur.fetchall()
            init_version = int(v[0]) if v else 0
        else:
            init_version = 0

        last_version = init_version

        batch = order_request.get(after=last_version)

        while len(batch) > 0:

            if Pipe.seconds(batch[len(batch)-1]["consignment_date"]) > cutoff:

                for order in batch:

                    if Pipe.seconds(order["consignment_date"]) > cutoff:
                        attrs = self._extract_attributes(order)
                        Pipe.put_sql(self.conn, attrs, "orders")

                    last_version = order["version"]
            else:
                last_version = batch[-1]["version"]

            batch = order_request.get(after=last_version)

        self._update_order_products(init_version, cutoff)

    ############################
    ## Order Products methods ##
    ############################

    def _extract_product_attributes(self, order_products, order_id):
        attrs = []
        for product in order_products:
            attrs.append({
                "order_id": order_id,
                "product_id": product["product_id"],
                "count": product["count"],
                "status": product['status']
            })
        return attrs

    def _update_order_products(self, init_version, cutoff):
        self.cur.execute("SELECT id FROM orders WHERE version > %s AND date > %s", init_version, cutoff)
        ids = self.cur.fetchall()

        for id in ids:
            order_products = order_request.get(page=f"{id[0]}/products")
            attrs = self._extract_product_attributes(order_products, id[0])

            Pipe.put_sql_many(self.conn, attrs=attrs, table="order_products")