document.addEventListener('DOMContentLoaded', () => {
    const isUserLoggedIn = document.body.dataset.userLoggedIn === 'true';

    // Helper to add Edit button column conditionally
    function addEditColumn(columns, entity) {
        if (isUserLoggedIn) {
            columns.push({
                title: "Edit",
                formatter: function(cell) {
                    const id = cell.getRow().getData().id;
                    return `<a href="/${entity}/edit/${id}" class="btn btn-sm btn-outline-primary">Edit</a>`;
                },
                hozAlign: "center",
                width: 90,
                headerSort: false,
                frozen: true  // optional: keep edit at left/right
            });
        }
    }

    // Deck Table
    const deckTable = document.getElementById('deckTable');
    if (deckTable) {
        const columns = [
            {title: "Deck Name", field: "deck_name", sorter: "string", headerFilter: "input"},
            {title: "Color Identity", field: "color_identity", sorter: "string", width: 130, hozAlign: "center"},
            {title: "Owner", field: "deck_owner", sorter: "string", width: 150},
            { 
                title: "Win Rate", 
                field: "win_rate", 
                sorter: "number", 
                width: 120,
                formatter: function(cell) {
                    const value = Number(cell.getValue()) || 0;
                    return (value * 100).toFixed(1) + "%";
                },
                headerFilter: "input"
            }
        ];
        addEditColumn(columns, "deck");

        new Tabulator("#deckTable", {
            ajaxURL: "/api/decks",
            layout: "fitColumns",
            pagination: "local",
            paginationSize: 25,
            paginationSizeSelector: [10, 25, 50, 100],
            rowHeight: 60,
            columns: columns,
            rowFormatter: function(row) {
                const winRate = Number(row.getData().win_rate) || 0;
                if (winRate > 0.5) row.getElement().style.backgroundColor = "#d4edda";
                else if (winRate > 0.3) row.getElement().style.backgroundColor = "#fff3cd";
            }
        });
    }

    // Player Table
    const playerTable = document.getElementById('playerTable');
    if (playerTable) {
        const columns = [
            {title: "ID", field: "id", sorter: "number", width: 80},
            {title: "Player Name", field: "player_name", sorter: "string", headerFilter: "input"},
            {title: "Wins", field: "wins", sorter: "number", width: 100},
            {title: "Total Games", field: "total_games", sorter: "number", width: 120},
            { 
                title: "Win Rate", 
                field: "win_rate", 
                sorter: "number", 
                width: 120,
                formatter: function(cell) {
                    const value = Number(cell.getValue()) || 0;
                    return (value * 100).toFixed(1) + "%";
                },
                headerFilter: "input"
            }
        ];
        addEditColumn(columns, "player");

        new Tabulator("#playerTable", {
            ajaxURL: "/api/players",
            layout: "fitColumns",
            pagination: "local",
            paginationSize: 25,
            paginationSizeSelector: [10, 25, 50, 100],
            rowHeight: 60,
            columns: columns
        });
    }
});
