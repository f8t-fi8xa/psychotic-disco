import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";

const tbody = document.querySelector("#product-tb");
const theaderRow = document.querySelector("#product-thr")
const prodName = document.querySelector("#p-name");
const prodPriceMin = document.querySelector("#p-price-min");
const prodPriceMax = document.querySelector("#p-price-max");
const prodSupplier = document.querySelector("#p-supplier");
const prodCountMin = document.querySelector("#p-count-min");
const prodCountMax = document.querySelector("#p-count-max");
const prodCategory2 = document.querySelector("#p-cat2");
const prodCategory3 = document.querySelector("#p-cat3");
const prodForm = document.querySelector("#i-form");

let container = document.querySelector("#graph-container");


const keys = Array.from(theaderRow.children, (e) =>
    e.textContent.toLowerCase().replace(" ", "_"))

function format(elements) {
    let formattedElements = [];
    for (let e of elements) {
        let s = e.value || "";
        switch (e.type) {
            case "text": {
                s = s.replace(" ", "%");
                s = `%${s}%`;
                break;
            }
            case "number": {
                s = +s;
            }
        }
        formattedElements.push(s);
    }
    return formattedElements;
}

prodForm.addEventListener("submit", function (event) {
    event.preventDefault();
    let query =
        `SELECT su.name AS seller, p.category_2, p.category_3, p.sku, p.name, p.price, i.count
         FROM products AS p JOIN inventory AS i ON p.id = i.product_id
         JOIN suppliers AS su ON p.supplier_id = su.id
         WHERE (p.name LIKE ? OR p.sku LIKE ?)
         AND p.price >= ? AND (p.price <= ? OR ? = 0)
         AND su.name LIKE ?
         AND i.count >= ? AND (i.count <= ? OR ? = 0)
         AND p.category_2 LIKE ? AND p.category_3 LIKE ?`;

    let params = format([
        prodName, prodName,
        prodPriceMin, prodPriceMax, prodPriceMax,
        prodSupplier,
        prodCountMin, prodCountMax, prodCountMax,
        prodCategory2, prodCategory3
    ]);
    tbody.replaceChildren();





    window.databaseAPI.fetchData(query, params).then(result => {
        const placeholders = result.map(() => "?");
        let gq =
            `SELECT p.sku,
        strftime('%Y-%m', sale_date, 'unixepoch') as month, 
        SUM(sp.count) as sales 
        FROM sales as s
        JOIN sale_products sp on s.id = sp.sale_id
        JOIN products p on sp.product_id = p.id
        WHERE p.sku in (${placeholders}) GROUP BY month, p.sku ORDER BY p.sku `;

        let gp = result.map(line => line.sku);
        window.databaseAPI.fetchData(gq, gp).then(r => {

            let data = r.reduce((acc, {sku, month, sales}) => {

                if (!acc[sku]) {
                    acc[sku] = []
                }
                acc[sku].push({sku: sku, month: new Date(month), sales: sales});
                return acc;
            }, {});

            let marks = []
            for (let product in data) {
                marks.push(Plot.line(data[product], {x: "month", y: "sales", stroke: "sku"}));
            }

            const plot = Plot.plot({
                x: {},

                marks: marks,

                color: {
                    legend: true,
                    label: "Product ID"
                }
            });

            if (container.firstChild) container.replaceChildren()
            container.appendChild(plot);
        })
        result.forEach(line => {
            addRow(tbody, line)
        });
    });
});

function addRow(element, values) {
    let row = document.createElement("tr");

    for (let key of keys) {
        let cell = document.createElement("td");
        cell.textContent = values[key];
        row.appendChild(cell);
    }
    element.appendChild(row);
}