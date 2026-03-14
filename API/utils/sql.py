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
            end_str += f"\nORDER BY {','.join(fields)} {direction}"
        if limit:
            end_str += f"\nLIMIT {limit}"
    return end_str

def make_select(query):
    if not query:
        return ''
    fields = ",".join([_make_field(field) for field in query["fields"]])
    main_table = _make_table(query['main_table'], main=True)
    joins = "\n".join([_make_table(table) for table in query["tables"]])
    conditions = "\nAND ".join([_make_condition(condition) for condition in query["conditions"]])
    end = _make_end(query['end']) if query.get("end") else ''

    query_str = f'''
    SELECT {fields} FROM {main_table} {joins} WHERE {conditions} {end}
    '''
    return query_str