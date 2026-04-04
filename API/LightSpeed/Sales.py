from . import _Pipe as Pipe

sale_request = Pipe.Request("sales")

class Sales:
    def __init__(self, conn, cur=None):
        self.conn = conn
        self.cur = conn.cursor() if cur is None else cur
    
    def _extract_attributes(self, sale):
        attrs = {
            "id": sale["id"],
            "register_id": sale["register_id"],
            "customer_id": "",
            "date": Pipe.seconds(sale["sale_date"]),
            "total_price": sale["total_price"],
            "invoice_number": sale["invoice_number"],
            "status": sale["status"],
            "version": sale["version"]
        }
        return attrs

    def update(self, append=True):
        print("Updating sales...")

        self.cur.execute("SELECT cutoff FROM config LIMIT 1")
        c = self.cur.fetchall()
        cutoff = int(c[0][0]) if c and c[0] else 0
        if append:
            self.cur.execute("SELECT version FROM sales ORDER BY version DESC LIMIT 1")
            v = self.cur.fetchall()
            last_version = int(v[0][0]) if v and v[0] else 0
        else:
            last_version = 0

        batch = sale_request.get(after=last_version)

        while len(batch) > 0:

            if Pipe.seconds(batch[-1]["sale_date"]) > cutoff:

                for sale in batch:
                    if Pipe.seconds(sale["sale_date"]) > cutoff:
                        sale_attrs = self._extract_attributes(sale)
                        product_attributes = self._extract_product_attributes(sale)

                        Pipe.put_sql(self.conn, sale_attrs, "sales")
                        Pipe.put_sql_many(self.conn, product_attributes, "sale_products")

                    last_version = sale["version"]
            else:
                last_version = batch[-1]["version"]
            batch = sale_request.get(after=last_version)

    ############################
    ## Sale Products methods ###
    ############################

    def _extract_product_attributes(self, sale):
        attr_list = []
        for product in sale['line_items']:
            attr_list.append({
                "sale_id": sale['id'],
                "product_id": product["product_id"],
                "discount_total": product["discount_total"],
                "price_total": product["price_total"],
                "cost_total": None,
                "tax_total": product["tax_total"],
                "count": product["quantity"],
                "status": product["status"]
            })
        return attr_list

