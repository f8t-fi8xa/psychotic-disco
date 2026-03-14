from . import _Pipe as Pipe

register_request = Pipe.Request("registers")

class Registers:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()

    def _extract_attributes(self, register):
        attrs = {
            "id": register['id'],
            "name": register['name'],
            "invoice_sequence": register['invoice_sequence'],
            "open": register['is_open'],
            "version": register['version']
        }
        return attrs

    def update(self):
        print("Updating registers...")

        for register in register_request.get():
            attrs = self._extract_attributes(register)
            Pipe.put_sql(self.conn, attrs, "registers")