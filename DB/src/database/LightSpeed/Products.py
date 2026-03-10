from . import _Pipe as Pipe
from datetime import datetime
import json

product_request = Pipe.Request("products")
inventory_request = Pipe.Request("inventory")

with open(r"C:\Users\liams\Gallery\DB\resources\Info.json") as file:
    info = json.load(file)

class Products:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()
    
    def _extract_attributes(self, product):
        if product['sku'] == 'vend-internal-gift-card':
            categories = ["Merchandise", "Promotional", ""]

        elif product['product_category']:
            categories = [c['name'] for c in product['product_category']['category_path']]
            categories += [""] * (3 - len(categories))
        else:
            categories = ["", "", ""]

        if len(product['categories']) > 0:
            tag = product['categories'][0]
            type = 'donation' if 'donation' == tag['name'] else 'merchandise'
        else: 
            type = 'merchandise'

        attrs = {
            "id": product["id"],
            "sku": product["sku"],
            "name": product["name"],
            "variant_name": product["variant_name"],
            "has_variants": product["has_variants"],
            "variant_count": product["variant_count"],
            "description": product["description"],
            "handle": product["handle"],
            "brand": None, # product["brand"] is type dict
            "has_inventory": product["has_inventory"],
            "is_composite": product["is_composite"],
            "category_1": categories[0],
            "category_2": categories[1],
            "category_3": categories[2],
            "supplier_id": product["supplier"]["id"] if product["supplier"] else None,
            "supplier_code": product["supplier_code"],
            "price": product["price_excluding_tax"],
            "updated_at": Pipe.seconds(product["updated_at"]),
            "created_at": Pipe.seconds(product["created_at"]),
            "deleted_at": Pipe.seconds(product["deleted_at"]) if product["deleted_at"] else None,
            "source": product["source"],
            "type": type,
            "account_code": product["account_code"],
            "account_code_purchase": product["account_code_purchase"],
            "supply_price": product["supply_price"],
            "in_store": product["active"],
            "online": product["ecwid_enabled_webstore"],
            "loyalty_amount": product["loyalty_amount"],
            "weight": product["weight"],
            "weight_unit": product["weight_unit"],
            "length": product["length"],
            "width": product["width"],
            "height": product["height"],
            "dimensions_unit": product["dimensions_unit"],
            "version": product["version"]
        }
        return attrs
    
    def _extract_item_attributes(self, product):
        if product['source'] == 'ecw:1596871B12679000':
            type = 'shipping_handling'
        elif product['source'] == 'SYSTEM' and product['name'] == 'Discount':
            type = 'discount'
        else:
            type = None

        active = True

        attrs = {
            "id": product["id"],
            "name": product["name"],
            "description": product["description"],
            "price": product["price_excluding_tax"],
            "updated_at": Pipe.seconds(product["updated_at"]) if product["updated_at"] else None,
            "created_at": Pipe.seconds(product["created_at"]) if product["created_at"] else None,
            "deleted_at": Pipe.seconds(product["deleted_at"]) if product["deleted_at"] else None,
            "source": product["source"],
            "type": type,
            "active": active,
            "version": product["version"]
        }
        return attrs

    def update(self):
        print("Updating products...")

        batch = product_request.get(deleted=True)

        while len(batch) > 0:
            for product in batch:
                updated = Pipe.seconds(product["updated_at"]) if not None else 0
                last_updated = Pipe.seconds(info['last_updated']) if info['last_updated'] else 0
                last_updated = 0

                if updated > last_updated:
                    if product['source'] in ['USER', 'B2B_NUORDER']:
                        attrs = self._extract_attributes(product)
                        Pipe.put_sql(self.conn, attrs, "products")
                        variant_attr_list = self._extract_variant_attributes(product)
                        Pipe.put_sql_many(self.conn, variant_attr_list, "product_variants")

                    elif product['source'] not in ['INTEGRATION-SYSTEM', 'SAMPLE']:
                        attrs = self._extract_item_attributes(product)
                        Pipe.put_sql(self.conn, attrs, "service_items")

                last_version = product["version"]
            batch = product_request.get(after=last_version, deleted=True)
        self._update_inventory()
        
        with open(r"C:\Users\liams\Gallery\DB\resources\Info.json", 'w') as file:
            info['last_updated'] = datetime.now().isoformat()
            json.dump(info, file, indent=4)

    ############################
    ## Variant methods #######
    ############################

    def _extract_variant_attributes(self, product):
        attr_list = []
        for option in product['variant_options']:
            attrs = {
                "product_id": product['id'],
                "option_name": option['name'],
                "option_value": option['value']
            }
            attr_list.append(attrs)
        return attr_list

    ############################
    ## Inventory methods #######
    ############################

    def _extract_inventory_attributes(self, product):
        attrs = {
            "product_id": product['product_id'],
            "count": product['current_amount']
        }
        return attrs

    def _update_inventory(self):
        batch = inventory_request.get()

        while len(batch) > 0:
            for product in batch:
                attrs = self._extract_inventory_attributes(product)
                Pipe.put_sql(self.conn, attrs, "inventory")

                last_version = product['version']
            batch = inventory_request.get(after=last_version)