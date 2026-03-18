import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";
import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
import {DateTime} from "https://cdn.jsdelivr.net/npm/luxon@3.4.4/+esm";

const API_URL = "https://psychotic-disco-production.up.railway.app"

export function format(input_element, default_value=null, field=null) {
    let input = input_element.value;
    if (default_value && input_element.value == '') input = default_value;

    if (input_element.type == "text") {
        if (!field) {
            input = input.replace(/ /g, "%");
            input = `%${input}%`;
            return input
        }
        // split input into array of logic gates and values
        // _ functions as empty string
        let values = input
            .replace(/(\s|^)-/g, " NOT")
            .replace(/\+/g, "AND")
            .replace(/\|/g, "OR")
            .replace(/_/g, "")
            .trim()
            .split(/ (?=\(|NOT|AND|OR)|(?<=\)|NOT|AND|OR) /);
        
        let result = {operator: '', terms: []};
        let stack = [result];
    
        values.forEach((item, i) => {
            if (item == 'AND' || item == 'OR') {
                stack[stack.length-1].operator = item;

                if (values[i+2] != ")" && values[i+3] != ')') {
                    let new_condition = {operator: '', terms: []};
                    stack[stack.length-1].terms.push(new_condition);
                    stack.push(new_condition);
                }
            }
            else if (item == '(') {
                let new_condition = {operator: '', terms: []};
                stack[stack.length-1].terms.push(new_condition);
                stack.push(new_condition);
            }
            else if (item == ')') {
                stack.pop();
            }
            else if (item != 'NOT') {
                if ((default_value != null) && item == '') {
                    // if the input is left blank and default value not null, 
                    // the default value is used
                    item = default_value; 
                }
                item = item.replace(/ /g, "%");
                item = `'%${item}%'`;
                let o = (i > 0 && values[i-1] === 'NOT') ? 'NOT LIKE': 'LIKE';
                stack[stack.length-1].terms.push({operator: o, terms: [field, item]});
            }
        });
        return result;
    }
    return input;
}

export class FieldSet {
    constructor(fields, onFinish = null) {
        this.fields = fields
        this.onFinish = onFinish
    }

    process(data, container) {
        for (let row of data) {
            let tr = document.createElement("tr");

            for (let field of this.fields) {
                if (Object.keys(row).find(value => value == field.key)) field.handle(tr, row[field.key]);
                else tr.appendChild(document.createElement("td"));
            }
            container.appendChild(tr);
        }
        if (this.onFinish) this.onFinish();
    }
}

export class Field {

    constructor(key, type, callback = (row, value) => {}, add_to_table = true) {
        const types = {
            string: (value) => value ? value: '',
            money: (value) => value ? value.toFixed(2): "0.00",
            int: (value) => value ? value: 0,
            date: (value) => value ? new Date(value * 1000).toLocaleDateString(): "",
            bool: (value) => value ? "true": "false",
        }
        this.key = key; 
        this.format = types[type];
        this.callback = callback;
        this.add_to_table = add_to_table;
    }

    handle(row, value) {
        this.callback(row, value);
        if (this.add_to_table) {
            let cell = document.createElement("td");
            cell.textContent = this.format(value)
            row.appendChild(cell);
        }
    }
}

async function load(endpoint, params) {
    return (await fetch(`${API_URL}/${endpoint}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(params)
    })).json();
}

export async function load_table(params, fieldSet, container) {
    const result = await load("api/search", params);
    fieldSet.process(result, container);
}

let data_cache, args = {params: null, container: null, interval: null, start: null, end: null, preferences: null};

export async function update_parameters(values) {
    for (let key in values) {args[key] = values[key];}
}

export async function reset_cache() {
    data_cache = null;
}

export async function update_cache() {
    let result;
    if (data_cache) result = data_cache
    else {
        result = await load("api/sales/get", args.params);
        console.log(result);
        result.forEach(product => {
            let date = null;
            switch(args.interval) {
                case "week": {
                    date = DateTime.fromFormat(product.interval, "kkkk-'W'WW").toJSDate(); 
                break;}
                case "month": date = DateTime.fromFormat(product.interval, "yyyy-MM").toJSDate(); 
                break;
                case "year": date = DateTime.fromFormat(product.interval, "yyyy").toJSDate(); 
                break;
                case "quarter": {
                    const [y, q] = product.interval.split("-Q")
                    const m = (q - 1)*3;
                    date = new Date(y, m);
                    break;
                }
            }
            product.interval = date;
        })
        data_cache = result;
    };
    return result
}

export async function load_graph() {
    const result = await update_cache();
    
    let sorted = {};
    for (let product of result) {
        if (!product.grouping_label) product.grouping_label = "all";
        if (!sorted[product.grouping_label]) sorted[product.grouping_label] = [];
        sorted[product.grouping_label].push(product);
    }
    let interval_format = d => d;
    let interval_label = "Date";
    let domain;
    switch (args.interval) {
        case "week": domain = d3.timeWeek
            .range(args.start, args.end).map(date => {date.setDate(date.getDate() + 1); return date;});
            interval_format = d => d.toLocaleDateString();
            interval_label = "Week of";
            break;
        case "month": domain = d3.timeMonth
            .range(args.start, args.end);
            interval_format = d => DateTime.fromJSDate(d).toFormat("MMMM yyyy");
            interval_label = "Month";
            break;
        case "quarter": domain = d3.timeMonth
            .every(3).range(args.start, args.end); 
            interval_format = d => `Q${(d.getMonth()/4 + 1).toFixed(0)} ${d.getFullYear()}`;
            interval_label = "Quarter";
            break;
        case "year": domain = d3.timeYear
            .range(args.start, args.end);
            interval_format = d => d.getFullYear();
            interval_label = "Year";
            break;
    }
    let padded = {};
    for (let grouping in sorted) {
        if (!Object.keys(padded).find(k => k === grouping)) padded[grouping] = [];
        padded[grouping] = domain.map(date => {
            const match = sorted[grouping].find(p => p.interval.getTime() === date.getTime());
            if (match) return match;
            return {interval: date, quantity: 0, revenue: 0, grouping_label: grouping};
    });
    }
    const flattened = Object.values(padded).flat(1);

    const plot = Plot.plot({
        x: {
            type: 'time',
            tickRotate: 45,
            ticks: d3.timeYear.range(args.start, args.end),
            tickFormat: d3.timeFormat("%Y"),
            grid: true
        },
        marks: [
            Plot.ruleY([0]),
            Plot.line(flattened, {
                x: "interval", 
                y: metric, 
                stroke: "grouping_label"
            }), 
            ...(args.preferences ? [Plot.dot(flattened, {
                x: {value: "interval", label: interval_label}, 
                y: metric, 
                r: args.preferences.radius, 
                fill: {value: "grouping_label", label: args.params.sales.grouping}, 
                stroke: {value: "grouping_label", label: args.params.sales.grouping}, 
                tip: {
                    format: {
                        x: d => interval_format(d)
                },
            }
        }
            )]: [])
        ],
        marginBottom: 60
    });

    if (args.container.firstChild) args.container.replaceChildren();
    args.container.appendChild(plot);
};


export async function update() {
    return fetch(`${API_URL}/api/update`, {
        method: "POST",
        headers: {
            "Accept": "application/json"
        }
    })
};

export function sort_table(table, col) {
    const data = table.children[0].children[0].children[col].dataset;
    let tbody = table.children[1];
    let rows = Array.from(tbody.rows);

    rows.sort((a, b) => {
        const aText = a.cells[col].innerText;
        const bText = b.cells[col].innerText;
        if (!aText) return -1;
        switch (data.type) {
            case "string": return aText.localeCompare(bText);
            case "number": return parseFloat(aText) - parseFloat(bText);
            case "bool": return aText.localeCompare(bText);
            case "date": {
                const aDate = aText.split("/").map(value => parseInt(value));
                const bDate = bText.split("/").map(value => parseInt(value));
                
                const aTime = new Date(aDate[2], aDate[0]-1, aDate[1]).getTime();
                const bTime = new Date(bDate[2], bDate[0]-1, bDate[1]).getTime();
                return aTime - bTime;
            }
        }
    });

    if (tbody.getAttribute("sorted") == col) {
        rows.reverse();
        tbody.removeAttribute("sorted");
    }
    else tbody.setAttribute("sorted", col);

    rows.forEach(row => tbody.appendChild(row));
}