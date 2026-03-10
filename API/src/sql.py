def check():
    pass

def _make_field(field: dict[str, str]):
    name = field.get("name", '')
    func = field.get("func")
    alias = field.get("alias")

    field_str = name

    if func:
        field_str = f"{func}({field_str})"

    if alias:
        field_str = f"{field_str} AS {alias}"
    return field_str

def _make_table(table, main=False):
    name = table.get("name", '')
    alias = table.get("alias")
    join_type = table.get("join_type")
    link = table.get("link")

    if main:
        table_str = name
    elif join_type:
        table_str = join_type + " JOIN " + name
    else:
        table_str = "JOIN " + name
        

    if alias:
        table_str += f" AS {alias}"

    if not main:
        table_str += f" ON {'='.join(link)}"

    return table_str

def _make_condition(condition):
    operator = f" {condition.get('operator')} "
    terms = []
    for term in condition.get("terms"):
        if type(term) == dict:
            term = _make_condition(term)
        terms.append(term)

    condition_str = f"({operator.join([str(t) for t in terms])})"

    return condition_str

def _make_end(end):
    group = end.get("group", '')
    order = end.get("order", '')

    end_str = '\n'
    if group:
        end_str += f"GROUP BY {','.join(group)}"

    if order:
        fields = order.get("fields")
        direction = order.get("direction", '')
        limit = order.get("limit")
        if fields:
            end_str += f"\nORDER BY {','.join(fields)}"
        if limit:
            end_str += f"\n{direction} LIMIT {limit}"
    return end_str

def make_select(query):
    fields = ",".join([_make_field(field) for field in query["fields"]])
    main_table = _make_table(query['main_table'], main=True)
    joins = "\n".join([_make_table(table) for table in query["tables"]])
    conditions = "\nAND ".join([_make_condition(condition) for condition in query["conditions"]])
    end = _make_end(query['end']) if query.get("end") else ''

    query_str = f'''
    SELECT {fields} FROM {main_table} {joins} WHERE {conditions} {end}
    '''
    return query_str

if __name__ == '__main__':
    query = {
        "fields": [
            {"name": 'grouping_value', "alias": "grouping_value"},
            {"name": "p.id", "alias": "product_id"},
            {"func": "SUM", "name": "sp.count", "alias": "quantity"},
            {"func": "SUM", "name": "sp.discount_total", "alias": "discount"},
            {"name": "i.count"},
            {"func": "SUM", "name": "sp.price_total", "alias": "revenue"},
            {"func": "MAX", "name": "s.date", "alias": "last_sold"},
        ],
        "main_table": {"name": "products", "alias": "p"},
        "tables": [
            {"name": "sale_products", "alias": "sp", "join_type": "LEFT", "link": ("p.id", "sp.product_id")},
            {"name": "sales", "alias": "s", "join_type": "LEFT", "link": ("sp.sale_id", "s.id")},
            {"name": "inventory", "alias": "i", "join_type": "LEFT", "link": ("p.id", "i.product_id")},
            {"name": "suppliers", "alias": "su", "join_type": "LEFT", "link": ("p.supplier_id", "su.id")},
        ],
        "conditions": [
            {"operator": "OR", "terms": (
                {"operator": "=", "terms": ("sp.status", 'CONFIRMED')}, 
                {"operator": "IS", "terms": ("sp.status", "NULL")}
            )},
            {"operator": "IS", "terms": ("p.deleted_at", "NULL")},
            {"operator": "OR", "terms": (
                {"operator": ">=", "terms": ("s.date", 'date_min')}, 
                {"operator": "<", "terms": ('date_min', 0)}
            )},
            {"operator": "OR", "terms": (
                {"operator": "<=", "terms": ("s.date", 'date_max')}, 
                {"operator": "<", "terms": ('date_max', 0)}
            )},
            {"operator": ">=", "terms": ("p.price", 'price_min')},
            {"operator": "<=", "terms": ("p.price", 'price_max')},
            {"operator": "OR", "terms": (
                {"operator": "AND", "terms": (
                    {"operator": ">=", "terms": ("i.count", 'count_min')}, 
                    {"operator": "<=", "terms": ("i.count", 'count_max')})}, 
                {"operator": "AND", "terms": [
                    {"operator": "IS", "terms": ("i.count", "NULL")}, 
                    {"operator": "<=", "terms": ('count_min', 0)}, 
                    {"operator": ">=", "terms": ('count_max', 0)}
        ]}
            )}
        ],
        "end": {
            "group": [
                "p.id"
                ],
            "order": {
                "fields": [
                    "p.id", "s.date"
                ],
                "direction": "DESC",
                "limit": 2
            }
        }
    }