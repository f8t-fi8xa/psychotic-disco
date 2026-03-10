export function sortTable(table, col) {
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