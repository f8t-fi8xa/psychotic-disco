import { check_creds } from "./auth.js";
check_creds()
import {sort_table, format, update, Field, FieldSet, reset_cache, update_parameters, load_table, load_graph} from "./data.js";

const i_portal = document.getElementById("i-portal");
const sPortal = document.getElementById("s-portal");
const i_view = document.getElementById("i-view");
const s_view = document.getElementById("s-view");
const form = document.getElementById("form");
const tbody = document.getElementById("product-tb");
const head_tr = document.getElementById("product-thr");
const rowCount = document.getElementById("row-count");
const name = document.getElementById("name");
const priceMin = document.getElementById("price-min");
const priceMax = document.getElementById("price-max");
const supplier = document.getElementById("supplier");
const countMin = document.getElementById("count-min");
const countMax = document.getElementById("count-max");
const cat1 = document.getElementById("cat1");
const cat2 = document.getElementById("cat2");
const cat3 = document.getElementById("cat3");
const inStoreActive = document.getElementById("in-store-active");
const inStoreInactive = document.getElementById("in-store-inactive");
const onlineActive = document.getElementById("online-active");
const onlineInactive = document.getElementById("online-inactive");
const lastSoldDayMin = document.getElementById("last-sold-day-min");
const lastSoldMonthMin = document.getElementById("last-sold-month-min");
const lastSoldYearMin = document.getElementById("last-sold-year-min");
const lastSoldDayMax = document.getElementById("last-sold-day-max");
const lastSoldMonthMax = document.getElementById("last-sold-month-max");
const lastSoldYearMax = document.getElementById("last-sold-year-max");
const saleDayMin = document.getElementById("sale-day-min");
const saleMonthMin = document.getElementById("sale-month-min");
const saleYearMin = document.getElementById("sale-year-min");
const saleDayMax = document.getElementById("sale-day-max");
const saleMonthMax = document.getElementById("sale-month-max");
const saleYearMax = document.getElementById("sale-year-max");
const quantityMin = document.getElementById("quantity-min");
const quantityMax = document.getElementById("quantity-max");
const revenueMin = document.getElementById("revenue-min");
const revenueMax = document.getElementById("revenue-max");
const register = document.getElementById("register");
const interval = document.getElementById("interval");
const metric = document.getElementById("metric");
const grouping = document.getElementById("grouping");
const toggle_dot = document.getElementById("toggle-dot");
const toggle_tip = document.getElementById("toggle-tip");
const radius = document.getElementById("radius");
const download = document.getElementById("download");
const main = document.getElementById("main");
const loading_screen = document.getElementById("loading-screen");

const side = document.getElementById("side");
const plus = document.getElementById("plus");
const plus_wrapper = document.getElementById("plus-wrapper");

function date_format(day, month, year, type) {
    const min = {day: 1, month: 1, year: 2020};
    const today = new Date();
    const max = {day: today.getDate(), month: today.getMonth()+1, year: today.getFullYear()};
    let date = {day: day, month: month, year: year};

    for (let key in date) {
        if (date[key] == '') {
            switch (type) {
                case 'min': date[key] = min[key]; break;
                case 'max': date[key] = max[key]; break;
                default: break;
            }
        }
        else if (date[key] < min[key]) date[key] = min[key];
        else if (date[key] > max[key]) date[key] = max[key];
    }
    return date;
}

toggle_dot.addEventListener("change", () => {
    if (toggle_dot.checked) update_parameters({preferences: {radius: +radius.value}});
    else update_parameters({preferences: null});
    load_graph();
})

radius.addEventListener("change", () => {
    if (toggle_dot.checked) {
        update_parameters({preferences: {radius: +radius.value}});
        load_graph();
    }
})

download.addEventListener("click", event => {
    event.preventDefault();
    let csv = Array.from(head_tr.children).map(e => e.textContent).join(",") + "\n";
    for (let row of tbody.children) {
        csv += Array.from(row.children).map(e => `"${e.textContent.replaceAll(/"/g, '""')}"`).join(",") + "\n";
    }
    const blob = new Blob([csv], {type: "text/plain"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = "table.csv";
    a.dispatchEvent(new Event("click"));
    a.click();

    URL.revokeObjectURL(url);
    a.remove();
})

i_portal.addEventListener("click", () => {
    i_view.classList.toggle('view--inactive');
    s_view.classList.toggle('view--inactive');
})

sPortal.addEventListener("click", () => {
    i_view.classList.toggle('view--inactive');
    s_view.classList.toggle('view--inactive');
})

form.addEventListener("submit", event => {
    event.preventDefault();
    const last_sold_min = [lastSoldDayMin.value, lastSoldMonthMin.value, lastSoldYearMin.value];
    const last_sold_max = [lastSoldDayMax.value, lastSoldMonthMax.value, lastSoldYearMax.value];
    const sale_min = [saleDayMin.value, saleMonthMin.value, saleYearMin.value];
    const sale_max = [saleDayMax.value, saleMonthMax.value, saleYearMax.value];

    const last_sold_blank = [...last_sold_min, ...last_sold_max].every(d => d == '');
    const sale_blank = [...sale_min, ...sale_max].every(d => d == '');

    const last_sold_date_min = date_format(...last_sold_min, last_sold_blank ? null : 'min');
    const last_sold_date_max = date_format(...last_sold_max, last_sold_blank ? null : 'max');
    const sale_date_min = date_format(...sale_min, sale_blank ? null : 'min');
    const sale_date_max = date_format(...sale_max, sale_blank ? null : 'max');

    lastSoldDayMin.value = last_sold_date_min.day;
    lastSoldMonthMin.value = last_sold_date_min.month;
    lastSoldYearMin.value = last_sold_date_min.year;

    lastSoldDayMax.value = last_sold_date_max.day;
    lastSoldMonthMax.value = last_sold_date_max.month;
    lastSoldYearMax.value = last_sold_date_max.year;

    saleDayMin.value = sale_date_min.day;
    saleMonthMin.value = sale_date_min.month;
    saleYearMin.value = sale_date_min.year;

    saleDayMax.value = sale_date_max.day;
    saleMonthMax.value = sale_date_max.month;
    saleYearMax.value = sale_date_max.year;
    tbody.replaceChildren();

    const params = {
        inventory: {
            price_min: +format(priceMin, -1*1e5),
            price_max: +format(priceMax, 1e5),
            count_min: +format(countMin, -1*1e5),
            count_max: +format(countMax, 1e5),
            name: format(name, '', 'p.name'),
            sku: format(name, '', 'p.sku'),
            last_sold_date_min: Date.UTC(lastSoldYearMin.value, lastSoldMonthMin.value - 1, lastSoldDayMin.value)/1000,
            last_sold_date_max: Date.UTC(lastSoldYearMax.value, lastSoldMonthMax.value - 1, lastSoldDayMax.value)/1000,
            supplier: format(supplier, '', 'su.name'),
            category_1: format(cat1, '', 'p.category_1'),
            category_2: format(cat2, '', 'p.category_2'),
            category_3: format(cat3, '', 'p.category_3'),
            in_store_active: +inStoreActive.checked,
            in_store_inactive: +inStoreInactive.checked,
            online_active: +onlineActive.checked,
            online_inactive: +onlineInactive.checked
        },
        sales: {
            sale_date_min: Date.UTC(saleYearMin.value, saleMonthMin.value - 1, saleDayMin.value)/1000,
            sale_date_max: Date.UTC(saleYearMax.value, saleMonthMax.value - 1, saleDayMax.value)/1000,
            quantity_min: +format(quantityMin, -1*1e5),
            quantity_max: +format(quantityMax, 1e5),
            revenue_min: +format(revenueMin, -1*1e5),
            revenue_max: +format(revenueMax, 1e5),
            register: register.value,
            interval: `iv.${interval.value}`,
            metric: metric.value,
            grouping: grouping.value
        }
        
    }

    const fieldSet = new FieldSet([
        new Field("seller", 'string'), 
        new Field("category_2", 'string'), 
        new Field("category_3", 'string'), 
        new Field("sku", 'string'), 
        new Field("name", 'string'), 
        new Field("price", 'money'), 
        new Field("count", 'int'), 
        new Field("in_store", 'bool'),
        new Field("online", 'bool'),
        new Field("created_at", 'date'), 
        new Field("last_sold", 'date'), 
        new Field("quantity", 'int'), 
        new Field("revenue", 'money'), 
        //new Field("discount", 'money'),
        //new Field("tax", 'money')
    ], function() {rowCount.textContent = tbody.children.length + " found";}
)

    load_table(params, fieldSet, tbody)
    const min = date_format(...sale_min, 'min');
    const max = date_format(...sale_max, 'max');
    const start = new Date(min.year, min.month - 1, min.day);
    const end = new Date(max.year, max.month - 1, max.day);

    update_parameters({
        params: params, container: s_view, 
        interval: interval.value, 
        start: start.getTime() < 0 ? min_range: start,
        end: end.getTime() < 0 ? max_range: end
    });
    reset_cache();
    load_graph();
});

document.querySelectorAll("#product-thr th").forEach((th, index) => {
    th.addEventListener("click", () => sort_table(i_view, index));
});

cat1.value = "Merchandise";
document.querySelectorAll('.filter-header').forEach(header => {
    header.addEventListener('click', () => {
    header.classList.toggle("active");
    });
});
// const side_bounds = side.getBoundingClientRect();
// const x = side_bounds.width - 60 - 10;
// const y = 85;
// plus_wrapper.style.top = y + "%";
// plus_wrapper.style.left = x + "px";

// const main_bounds = Object.fromEntries(
//     Object.entries(main.getBoundingClientRect().toJSON()).map(([k, v]) => ([k, v + "px"]))
// );
// loading_screen.style.display = "flex";
// loading_screen.style.top = main_bounds.y;
// loading_screen.style.left = main_bounds.x;
// loading_screen.style.width = main_bounds.width;
// loading_screen.style.height = main_bounds.height;
// update()
// .catch(err => console.log(err))
// .then(res => {
//     loading_screen.style.display = "none";
//     form.dispatchEvent(new Event("submit"));
//     toggle_dot.dispatchEvent(new Event("change"));
// });