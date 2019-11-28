
var chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/betMaster/' + betRoomNum + '/'
);

chatSocket.onmessage = function(e) {
    var data = JSON.parse(e.data);
    var btcAddress = document.querySelector("#walletChars").innerHTML;

    if (data['command'] === "init") {

        if (data['message']['awayTeamSpread'] < 0) {
            var awayTeamHeader = data['message']['awayTeam'] + " (" + data['message']['awayTeamSpread'] + ")";
            document.querySelector("#awayTeamHeader").innerHTML = awayTeamHeader;

            var homeTeamHeader = data['message']['homeTeam'] + " (+" + data['message']['homeTeamSpread'] + ")";
            document.querySelector("#homeTeamHeader").innerHTML = homeTeamHeader;

            document.querySelector("#spreadInfo").innerHTML = data['message']['awayTeamSpread'];

            document.querySelector("#betSelect").options[0].value = data['message']['awayTeamSpread'];
            document.querySelector("#betSelect").options[1].value = "+" + data['message']['homeTeamSpread'];

            document.querySelector("#myRange").min = Math.abs(data['message']['awayTeamSpread']) - 2;
            document.querySelector("#myRange").max = data['message']['homeTeamSpread'] + 2;
            document.querySelector("#myRange").value = data['message']['homeTeamSpread'];
            document.querySelector("#baseSpreadHolder").innerHTML = data['message']['homeTeamSpread'];

        } else {
            var awayTeamHeader = data['message']['awayTeam'] + " (+" + data['message']['awayTeamSpread'] + ")";
            document.querySelector("#awayTeamHeader").innerHTML = awayTeamHeader

            var homeTeamHeader = data['message']['homeTeam'] + " (" + data['message']['homeTeamSpread'] + ")";
            document.querySelector("#homeTeamHeader").innerHTML = homeTeamHeader;

            document.querySelector("#spreadInfo").innerHTML = "+" + data['message']['awayTeamSpread'];

            document.querySelector("#betSelect").options[0].value = "+" + data['message']['awayTeamSpread'];
            document.querySelector("#betSelect").options[1].value = data['message']['homeTeamSpread'];

            document.querySelector("#myRange").min = Math.abs(data['message']['homeTeamSpread']) - 2;
            document.querySelector("#myRange").max = data['message']['awayTeamSpread'] + 2;
            document.querySelector("#myRange").value = data['message']['awayTeamSpread'];
            document.querySelector("#baseSpreadHolder").innerHTML = data['message']['awayTeamSpread'];

        }
        
        for (var i = 0; i < data['pendingBets'].length; i++) {
            var bet = data['pendingBets'][i];
            //var offset = bet.offEven + 2;
            var offset = (bet.offEven * 2) + 4;
            if (bet.pick === "home") {
                var tableDivs = document.getElementById("homeTableHolder").getElementsByTagName("tbody");
                var row = tableDivs[offset].insertRow(tableDivs[offset].length);
                var cell1 = row.insertCell(0);
                var cell2 = row.insertCell(1);
                var cell3 = row.insertCell(2);

                cell1.innerHTML = bet.address;
                cell2.innerHTML = bet.amount;
                cell3.innerHTML = bet.id;
                cell3.style.display = "none";
            } else {

                var tableDivs = document.getElementById("awayTableHolder").getElementsByTagName("tbody");
                var row = tableDivs[offset].insertRow(tableDivs[offset].length);
                var cell1 = row.insertCell(0);
                var cell2 = row.insertCell(1);
                var cell3 = row.insertCell(2);

                cell1.innerHTML = bet.address;
                cell2.innerHTML = bet.amount;
                cell3.innerHTML = bet.id;
                cell3.style.display = "none";
            }
        }

        
    } else if (data['command'] === "addBet") {
        var offset = (data['message']['offEven'] * 2) + 4;
        if (data['message']['pick'] === "home") {
            updateTable("homeTableHolder", data, offset);

        } else {
            updateTable("awayTableHolder", data, offset);

        }
        if (btcAddress === data['message']['btcAddress']) {
            updateBalance(data['message']['newBalance']);
            alertify.notify('Bet pending. ' + data['message']['amount'] + ' added to queue.', 'custom', 5, function(){console.log('dismissed');});
        }

    } else if (data['command'] === "deleteBet") {
        var offset = (data['message']['offEven'] * 2) + 4;
        if (data['message']['pick'] === "home") {
            deleteTableRow("homeTableHolder", data, offset);
            
        } else {
            deleteTableRow("awayTableHolder", data, offset);
        }

        if (btcAddress === data['message']['better1'] || btcAddress === data['message']['better2']) {
            
            alertify.notify('Bet matched. ' + data['message']['amount'] + ' BTC confirmed.', 'custom', 5, function(){console.log('dismissed');});
            if (btcAddress === data['message']['better1']) {

                updateBalance(data['message']['newBalance']);
            }

        }
    } else if (data['command'] === "updateTable") {
        var offset = (data['message']['offEven'] * 2) + 4;
        if (data['message']['pick'] === "home") {
            updateTableRow("homeTableHolder", data, offset);

        } else {
            updateTableRow("awayTableHolder", data, offset);

        }
        if (btcAddress === data['message']['better1'] || btcAddress === data['message']['better2']) {
            alertify.notify('Bet matched. ' + data['message']['amount'] + ' BTC confirmed.', 'custom', 5, function(){console.log('dismissed');});

            if (btcAddress === data['message']['better1']) {
                updateBalance(data['message']['newBalance']);
            }
        }
    }
};

chatSocket.onclose = function(e) {
    console.error('Betroom socket closed unexpectedly');
};

function placeBet(username) {
    
    var select = document.querySelector("#betSelect");
    if (select.selectedIndex === 0) {
        var homeOrAway = "away";
    } else {
        var homeOrAway = "home";
    }
    var teamName = select.options[select.selectedIndex].text;

    var selectedSpread = document.querySelector("#spreadInfo").innerHTML;
    selectedSpread = selectedSpread.replace("+", "");
    var amount = document.querySelector("#btcConversion").value;
    var payout = (amount * 1.98).toFixed(8);

    chatSocket.send(JSON.stringify({
        'betRequest': {
            'username':username,
            'gameID':betRoomNum,
            'homeOrAway':homeOrAway,
            'teamName':teamName,
            'spread':selectedSpread,
            'amount':amount,
            'payout':payout
        }
    }));


}

function updateBalance(newBalance) {

    var balanceHeader = document.getElementById("balanceNotifier").innerHTML;
    var prevBalance = balanceHeader.slice(118);
    var newBalanceHeader = balanceHeader.replace(prevBalance, newBalance);
    document.getElementById("balanceNotifier").innerHTML = newBalanceHeader;


    var windowBalance = document.getElementById("balanceHeader").innerHTML;
    var windowPrevBalance = windowBalance.slice(95);
    var newWindowBalance = windowBalance.replace(windowPrevBalance, newBalance);
    document.getElementById("balanceHeader").innerHTML = newWindowBalance;

    calcMaxBet(conversionRate, newBalance);

    resetUI();
}