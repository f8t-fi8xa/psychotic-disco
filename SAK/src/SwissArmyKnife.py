from PIL import Image, ImageFont, ImageDraw, ImageOps
import time
import os
import math
import sqlite3
from barcode import Code128
from barcode.writer import ImageWriter
from tempfile import TemporaryDirectory
import textwrap
from database.LightSpeed import Products, Orders, Suppliers

class Metric:
    def __init__(self, screen_size: float, screen_resolution: tuple[float, float], label_sheet_size: tuple[float, float],
                 label_size: tuple[float, float], labels_per_row: int, labels_per_col: int,
                 label_margins: tuple[int, int], label_spacing: tuple[int, int]):
        self.LABELS_PER_SHEET = labels_per_row * labels_per_col
        self.PPI = math.sqrt(screen_resolution[0] ** 2 + screen_resolution[1] ** 2) / screen_size
        self.SCREEN_SIZE = screen_size
        self.SCREEN_RESOLUTION = screen_resolution
        self.LABEL_SHEET_SIZE = label_sheet_size
        self.LABEL_SIZE = label_size
        self.LABELS_PER_ROW = labels_per_row
        self.LABELS_PER_COL = labels_per_col
        self.LABEL_MARGINS = label_margins  # x, y
        self.LABEL_SPACING = label_spacing  # x, y

    def inches(self, px: int or tuple[int, int]) -> float or tuple[float, float]:
        if type(px) == int:
            return px / self.PPI
        return tuple(x / self.PPI for x in px)

    def pixels(self, _in: float or tuple[float, float]) -> int or tuple[int, int]:
        if type(_in) == float:
            return int(_in * self.PPI)
        else:
            return tuple(int(x * self.PPI) for x in _in)



m = Metric(screen_size=14.0,
           screen_resolution=(1920, 1080),
           label_sheet_size=(4.0, 6.0),
           label_size=(1.50, 0.75),
           labels_per_row=2, labels_per_col=7,
           label_margins=(0.375, 0.375),
           label_spacing=(0.25, 0.0))


class Barcode:
    def __init__(self, metric: Metric=m):
        self.metric = metric
        # pixels
        self.label_size = tuple[int, int](self.metric.pixels(self.metric.LABEL_SIZE))
        self.label_sheet_size = tuple[int, int](self.metric.pixels(self.metric.LABEL_SHEET_SIZE))

    def generate(self, name: str, sku: str, price: float):

        size = self.label_size
        price_str = f"${price:.2f}"

        options = {"write_text": False, "module_height": 4}

        # Create Barcode
        barcode = Code128(sku, writer=ImageWriter())
        temp = TemporaryDirectory()
        barcode.save(f"{temp.name}/{sku}", options=options)  # Saves the barcode as an image
        barcode_image = Image.open(f"{temp.name}/{sku}.png")
        ratio = barcode_image.height / barcode_image.width
        barcode_image = barcode_image.resize(size=(size[0] - 5, int(ratio * (size[0] - 5))))

        new_image = Image.new(mode="RGBA", size=size, color="white")

        sku_font = ImageFont.load_default(size=10)
        name_font = ImageFont.load_default(size=14)

        name_font_length = name_font.getlength(name)
        flpc = name_font_length / len(name)
        overflow = int(barcode_image.width / flpc)

        new_name = textwrap.fill(name, overflow)

        sku_width, sku_height = ImageDraw.Draw(new_image).textbbox((0, 0), sku, font=sku_font)[2:]
        name_width, name_height = ImageDraw.Draw(new_image).multiline_textbbox((0, 0), f"{new_name}\n{price_str}",
                                                                               font=name_font, align='center')[2:]

        y = 0
        x = int((size[0] - barcode_image.width) / 2)
        new_image.paste(barcode_image, (x, y))

        # Draw sku label
        y += barcode_image.height
        draw_sku = ImageDraw.Draw(new_image)
        sku_x = x + (barcode_image.width - sku_width) / 2
        sku_y = y
        draw_sku.text((sku_x, sku_y), sku, fill="black", font=sku_font)

        # Draw name label
        space = 1
        y += space + sku_height
        draw_name = ImageDraw.Draw(new_image)
        name_x = x + (barcode_image.width - name_width) / 2
        name_y = y
        draw_name.multiline_text((name_x, name_y), new_name + '\n' + price_str, fill="black", spacing=4, font=name_font,
                                 align='center')
        temp.cleanup()
        return new_image

    def create(self, attributes, save=False):
        images = []
        for a in attributes:
            for i in range(a["count"]):
                image = self.generate(a["name"], a["sku"], a["price"])
                images.append(image)

        self.generate_layout(images, save)

    def generate_layout(self, images, save=False):
        if not os.access("./images", mode=os.F_OK) and save:
            os.mkdir("./images")
        sheet = 0

        while True:
            new_image = Image.new(mode='L', color=255, size=self.label_sheet_size)

            col = 0
            y = self.metric.pixels(self.metric.LABEL_MARGINS[1])
            while col < 7:
                row = 0
                x = self.metric.pixels(self.metric.LABEL_MARGINS[0])
                while row < 2:
                    if row + 2 * col + 14 * sheet >= len(images):
                        if save:
                            new_image.save(f"./images/sheet {sheet}.png")
                        else:
                            new_image.show()
                        return
                    im = images[row + 2 * col + 14 * sheet]
                    new_image.paste(im=im, box=(x, y))
                    x += self.metric.pixels(self.metric.LABEL_SIZE[0] + self.metric.LABEL_SPACING[0])
                    row += 1
                y += self.metric.pixels(self.metric.LABEL_SIZE[1] + self.metric.LABEL_SPACING[1])
                col += 1
            if save:
                new_image.save(f"./images/sheet {sheet}.png")
            else:
                new_image.show()
            sheet += 1


if __name__ == "__main__":


    valid = False
    error_count = 0
    mode = None
    modes = ["Order", "Supplier", "Custom"]
    attrs = None
    save = True

    products = Products()
    orders = Orders()
    suppliers = Suppliers()

    #products.update()

    conn = sqlite3.Connection(r"C:\Users\liams\Gallery\SAK\resources\data.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    while not valid:
        mode = input("Enter mode (Order, Supplier, Custom):\n")
        if mode in modes:
            valid = True

        elif error_count < 4:
            error_count += 1
            print("YOU FOOL! Invalid mode.")
        else:
            print("Go take a break. Touch some grass.")
            time.sleep(10)
            exit()

    if mode == "Order":
        orders.update()
        order = input("Enter order reference:\n")

        cur.execute('''
            SELECT op.count, p.name, p.sku, p.price FROM orders AS o
            JOIN order_products AS op ON o.id = op.order_id
            JOIN products AS p ON op.product_id = p.id
            WHERE o.reference = ?''', [order])
        attrs = [dict(p) for p in cur.fetchall()]

    elif mode == "Supplier":
        suppliers.update()
        supplier = input("Enter supplier code:\n")
        
        cur.execute('''
            SELECT i.count, p.name, p.sku, p.price FROM suppliers AS s 
            JOIN products AS p ON s.id = p.supplier_id
            JOIN inventory AS i ON p.id = i.product_id
            WHERE s.name = ?''', [supplier])
        attrs = [dict(p) for p in cur.fetchall()]

    elif mode == "Custom":
        attrs = []
        line = input("Enter sku and count (sku, count):\n").upper().split(", ")
        condition = True
        while "DONE" not in line:
            if condition:
                sku, count = line
                cur.execute('''
                        SELECT p.name, p.price FROM products AS p
                        WHERE p.sku = ?''', [sku])

                attrs.append(
                    {
                        'sku': sku,
                        'count': int(count)
                        
                    } | dict(cur.fetchone())
                )
                    
            else:
                print("Invalid Seller")
            line = input("Enter sku and count (sku, count):\n").upper().split(", ")

    print(attrs)
    Barcode().create(attributes=attrs, save=save)