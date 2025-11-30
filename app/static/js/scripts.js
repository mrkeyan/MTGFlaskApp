document.addEventListener('DOMContentLoaded', () => {
    const isUserLoggedIn = document.body.dataset.userLoggedIn === 'true';
    const isUserAdmin = document.body.dataset.userIsAdmin === 'true';  // NEW

    // Helper to add Edit button column conditionally
    function addEditColumn(columns, entity) {
        if (isUserLoggedIn && isUserAdmin) {  // CHANGED: Admin only
            columns.push({
                title: " ",
                field: "edit",
                formatter: function(cell) {
                    const id = cell.getRow().getData().id;
                    return `<a href="/${entity}/edit/${id}" class="btn btn-sm btn-outline-primary">Edit</a>`;
                },
                hozAlign: "center",
                headerSort: false,
                resizable: false,
                width: 90,
                responsive: 0
            });
        }
    }

    // Deck Table
    const deckTable = document.getElementById('deckTable');
    if (deckTable) {
        const columns = [
            {title: "Deck Name", 
                field: "deck_name", 
                sorter: "string", 
                headerFilter: "input",
                responsive:0,
                resizable:false,
                headerWordWrap:true
            },
            {title: "Owner", field: "deck_owner", sorter: "string", width: 150,resizable:false},
            { 
                title: "Win Rate", 
                field: "win_rate", 
                sorter: "number", 
                width: 120,
                formatter: function(cell) {
                    const value = Number(cell.getValue()) || 0;
                    return (value * 100).toFixed(1) + "%";
                },
                responsive:0,
                resizable:false,
                headerWordWrap:true
                //,
                //headerFilter: "input"
            },
            {title: "Color Identity", field: "color_identity", sorter: "string", width: 130, hozAlign: "center",resizable:false, headerWordWrap:true}
        ];
        addEditColumn(columns, "deck");

        new Tabulator("#deckTable", {
            ajaxURL: "/api/decks",
            layout: "fitDataFill",
            responsiveLayout: "collapse",
            pagination: "local",
            paginationSize: 25,
            paginationSizeSelector: [10, 25, 50, 100],
            rowHeight: 60,
            columns: columns,
          /*   rowFormatter: function(row) {
                const winRate = Number(row.getData().win_rate) || 0;
                if (winRate > 0.5) row.getElement().style.backgroundColor = "#d4edda";
                else if (winRate > 0.3) row.getElement().style.backgroundColor = "#fff3cd";
            } */
        });
    }

    // Player Table
    const playerTable = document.getElementById('playerTable');
    if (playerTable) {
        const columns = [
            {title: "Player", field: "player_name", sorter: "string", responsive:0,resizable:false},
            {title: "Wins", field: "wins", sorter: "number", responsive:0,resizable:false},
            {title: "Total Games", field: "total_games", sorter: "number", responsive:2,resizable:false, headerWordWrap:true},
            { 
                title: "Win Rate", 
                field: "win_rate", 
                sorter: "number", 
                formatter: function(cell) {
                    const value = Number(cell.getValue()) || 0;
                    return (value * 100).toFixed(1) + "%";
                },
                 responsive:0,
                 resizable:false,
                 headerWordWrap:true
            }
        ];
        addEditColumn(columns, "player");

        new Tabulator("#playerTable", {
            ajaxURL: "/api/players",
            layout: "fitColumns",
            responsiveLayout: "collapse",
            pagination: "local",
            paginationSize: 25,
            paginationSizeSelector: [10, 25, 50, 100],
            rowHeight: 60,
            columns: columns
        });
    }
});