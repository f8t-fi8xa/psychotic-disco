import re

class Field:
    def __init__(self, field: dict[str, str], tables=[]):
        self.name = str(field.get("name", ''))
        self.func = str(field.get("func", ''))
        self.alias = str(field.get("alias", ''))

        p = '^[a-zA-Z0-9_]*$'
        alpha_num = _validate_field(self.name, tables) and re.match(p, self.func) and re.match(p, self.alias)
        if not alpha_num:
            print({"field": field})
            raise TypeError("Wrong type bud")

    def __repr__(self) -> str:
        field_str = self.name

        if self.func:
            field_str = f"{self.func}({field_str})"

        if self.alias:
            field_str = f"{field_str} AS {self.alias}"
        return field_str

class Table:
    def __init__(self, table: dict, is_main: bool = False):
        self.name = str(table.get("name", ''))
        self.alias = str(table.get("alias", ''))
        self.join_type = str(table.get("join_type", '')).upper()
        self.link = table.get("link")
        self.is_main = bool(is_main)

        correct_types = isinstance(self.link, (tuple, list)) if not is_main else True
        p = '^[a-zA-Z0-9_]*$'
        alpha_num_base = re.match(p, self.name) and re.match(p, self.alias) and re.match(p, self.join_type)
        if is_main:
            alpha_num = alpha_num_base
        elif correct_types and len(self.link) == 2:
            alpha_num = alpha_num_base and re.match(p, self.link[0]) and re.match(p, self.link[1])
        else:
            alpha_num = False
        if not correct_types or not alpha_num:
            print({"table": table, "is_main": is_main})
            raise TypeError("Wrong type bud")

    def __repr__(self) -> str:
        if self.is_main:
            table_str = self.name
        elif self.join_type:
            table_str = self.join_type + " JOIN " + self.name
        else:
            table_str = "JOIN " + self.name
            
        if self.alias:
            table_str += f" AS {self.alias}"

        if not self.is_main:
            table_str += f" ON {'='.join(self.link)}"

        return table_str
    
def _validate_field(term: str = '', tables: list[str] = []):
    if not tables:
        return False

    if not any([re.match(f'^{re.escape(table)}\\.[a-zA-Z0-9_]+$', term) for table in tables]):
        return False
    return True

class Condition:
    ALLOWED_OPERATORS = {
    'AND', 'OR',                           # logical
    '=', '!=', '<', '>', '<=', '>=',       # comparison
    'IS', 'IS NOT',                        # is
    'IN', 'NOT IN',                        # in
    'LIKE', 'NOT LIKE',                    # like
    'BETWEEN', 'NOT BETWEEN'               # between
    }
    def __init__(self, condition: dict, tables=[]):
        operator = str(condition.get('operator', '')).upper()
        self.terms = []
        self.params = []
        init_terms = condition.get("terms")

        correct_types = operator in self.ALLOWED_OPERATORS and isinstance(init_terms, list)
        if not correct_types:
            print({"condition": condition, "tables": tables})
            raise TypeError("Wrong type bud")
        
        for term in init_terms:
            if isinstance(term, dict):
                term = Condition(term)
                term_str = term.condition_str
                params = term.params
            elif _validate_field(term, tables):
                term_str = term
                params = []
            elif isinstance(term, (list, tuple)):
                term_str = f"({','.join(['?']*len(term))})"
                params = [str(p) for p in term]
            else:
                term_str = '?'
                params = [str(term)]
            self.terms.append(term_str)
            self.params += params
        self.operator = f" {operator} "

        self.condition_str = f"({self.operator.join([term for term in self.terms])})"
    
    def __repr__(self):
        return self.condition_str

class End:
    def __init__(self, end):
        self.group = end.get("group", [])
        self.order = end.get("order", {})
        correct_iter_types = isinstance(self.group, list) and isinstance(self.order, dict)
        if not correct_iter_types:
            print({"end": end})
            raise TypeError("Wrong type bud")
        
        self.fields = self.order.get("fields", [])
        self.direction = str(self.order.get("direction", '')).upper()
        self.limit = str(self.order.get("limit", ''))

        p = '^[a-zA-Z0-9_]*$'

        correct_types = isinstance(self.fields, list) and None not in [re.match(p, str(field)) for field in self.fields] and self.direction in ['', 'ASC', 'DESC'] and re.match('^[0-9]*$', self.limit)
        if not correct_types:
            print({"end": end})
            raise TypeError("Wrong type bud")
        
    def __repr__(self):
        end_str = '\n'
        if self.group:
            end_str += f"GROUP BY {','.join(self.group)}"

        if self.fields:
            end_str += f"\nORDER BY {','.join(self.fields)} {self.direction}"
        if self.limit:
            end_str += f"\nLIMIT {self.limit}"
        return end_str

def make_select(query):
    try:
        main_table = Table(query['main_table'], is_main=True)
        prefixes = [main_table.name, main_table.alias]
        for table in query['tables']:
            t = Table(table)
            prefixes += [t.name, t.alias]
        main_table = str(main_table)
        fields = ",".join([str(Field(field, prefixes)) for field in query["fields"]])
        joins = "\n".join([str(Table(table)) for table in query["tables"]])
        conditions = "\nAND ".join([str(Condition(condition, prefixes)) for condition in query["conditions"]])
        end = str(End(query['end'])) if query.get("end") else ''

        params = []
        for condition in query['conditions']:
            params += Condition(condition, prefixes).params
    except (KeyError, TypeError) as e:
        print(query)
        raise TypeError("YOU DONE MESSED UP A-ARON")

    query_str = f'''
    SELECT {fields} FROM {main_table} {joins} WHERE {conditions} {end}
    '''
    return query_str, params