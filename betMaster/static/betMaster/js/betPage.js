function initPage(encodedImg) {

    var formattedString = encodedImg.replace(/&quot;/g, "");
    var imgSrc = 'data:image/png;base64,' + formattedString;
    document.getElementById("qrCode").src = imgSrc;
    try {
        document.getElementById("initQRCodeImg").src = imgSrc;
    } catch(e) {
        // Not on initProfilePage
    }

}

function calcMaxBet(conversionRate, balance) {
    var maxUsdBet = ((conversionRate * balance) - 1).toFixed(2);
    if (maxUsdBet < 0) {
        maxUsdBet = 0.00;
    }
    document.getElementById("maxBet").innerHTML = "Max Bet: $" + parseFloat(maxUsdBet);
}

function convertToBtc(rate) {
    
    var usdAmount = parseFloat(document.getElementById("usdInput").value);
    var btcAmount = usdAmount / rate;
    btcAmount = btcAmount.toFixed(8);
    document.getElementById("btcConversion").value = btcAmount;

    var btcPayout = (btcAmount * 1.98).toFixed(8);
    var usdPayout = (usdAmount * 1.98).toFixed(2);
    var usdString = parseFloat(usdPayout);

    var maxBet = document.getElementById("maxBet").innerHTML;
    maxBet = maxBet.slice(10);
    var maxFloat = parseFloat(maxBet);
    
    if (usdAmount >= maxFloat) {
        document.getElementById("placeBetBtn").disabled = true;
        document.getElementById("errorMessage").innerHTML = "Bet exceeds account balance";
        document.getElementById("errorMessage").style.display = "block";
        document.getElementById("usdInput").style.border = "2px solid red";

    } else {
        document.getElementById("placeBetBtn").disabled = false;
        document.getElementById("errorMessage").style.display = "none";
        document.getElementById("usdInput").style.border = "2px solid white";
    }
    document.getElementById("usdPayout").value = usdString;
    document.getElementById("btcPayout").value = btcPayout;

    

}

function updateTable(selector, data, offset) {

    var tableDivs = document.getElementById(selector).getElementsByTagName("tbody");

    var row = tableDivs[offset].insertRow(tableDivs[offset].length - 1);
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    var cell3 = row.insertCell(2);

    // Add some text to the new cells:
    cell1.innerHTML = data['message']['btcAddress'];
    cell2.innerHTML = data['message']['amount'];
    cell3.innerHTML = data['message']['id'];
    cell3.style.display = "none";
}

function updateTableRow(selector, data, offset) {
    var tableDivs = document.getElementById(selector).getElementsByTagName("tbody");
    var correctTable = tableDivs[offset];
    for (var i = 0; i < correctTable.rows.length; i++) {
        var idCellContent = correctTable.rows[i].cells[2].innerHTML;
        if (parseInt(idCellContent) === parseInt(data['message']['id'])) {
            correctTable.rows[i].cells[1].innerHTML = data['message']['newAmount'];
        }
    }
}

function deleteTableRow(selector, data, offset) {
    var tableDivs = document.getElementById(selector).getElementsByTagName("tbody");
    var correctTable = tableDivs[offset];
    for (var i = 0; i < correctTable.rows.length; i++) {
        var idCellContent = correctTable.rows[i].cells[2].innerHTML;
        if (parseInt(idCellContent) === parseInt(data['message']['id'])) {
            correctTable.deleteRow(i);
        }
    }
}

function updateBetSelection() {

    var spreadElement = document.getElementById("spreadInfo");
    var teamSelector = document.getElementById("betSelect");
    var selectOptions = teamSelector.options;
    var selectedIndex = teamSelector.selectedIndex;

    spreadElement.innerHTML = selectOptions[selectedIndex].value;
}

function resetUI() {
    document.getElementById("usdInput").value = "";
    document.getElementById("btcConversion").value = "0.00";
    document.getElementById("usdPayout").value = "0.00";
    document.getElementById("btcPayout").value = "0.00";
    document.getElementById("placeBetBtn").disabled = "true";
}


// Update page when slider value changes
var slider = document.getElementById("myRange");


// Update the current slider value (each time you drag the slider handle)
slider.oninput = function() {
    document.getElementById("selectedSpread").innerHTML = slider.value;
    var baseSpread = parseFloat(document.getElementById("baseSpreadHolder").innerHTML);
    var offset = ((slider.value - baseSpread) * 2) + 4;
    var homeDivs = document.getElementById("homeTableHolder").getElementsByClassName("table");
    for (var i = 0; i < homeDivs.length; i++) {
        if (i === offset) {
            homeDivs[i].style.display = "block";
            
        } else {
            homeDivs[i].style.display = "none";
        }
    }

    var awayDivs = document.getElementById("awayTableHolder").getElementsByClassName("table");
    for (var i = 0; i < awayDivs.length; i++) {
        if (i === offset) {
            awayDivs[i].style.display = "block";
        } else {
            awayDivs[i].style.display = "none";

        }
    }
    

    var awayTeamHeader = document.getElementById("awayTeamHeader").innerHTML;
    var homeTeamHeader = document.getElementById("homeTeamHeader").innerHTML;
    

    var spreadIndex = homeTeamHeader.indexOf("(");
    var posNegChar = homeTeamHeader[spreadIndex + 1];
    var spreadElement = document.getElementById("spreadInfo");
    var teamSelector = document.getElementById("betSelect");
    var selectOptions = teamSelector.options;
    var selectedIndex = teamSelector.selectedIndex;

    if (posNegChar === "+") {

        if (slider.value > 0) {
            selectOptions[0].value = "-" + parseFloat(slider.value);
            selectOptions[1].value = "+" + parseFloat(slider.value);
            var newHomeTeamHeader = homeTeamHeader.slice(0, spreadIndex) + "(+" + parseFloat(slider.value) + ")";
            var newAwayTeamHeader = awayTeamHeader.slice(0, awayTeamHeader.indexOf("(") - 1) + " (-" + parseFloat(slider.value) + ")";
            
        } else if (slider.value === 0) {
            selectOptions[0].value = parseFloat(slider.value);
            selectOptions[1].value = parseFloat(slider.value);
            var newHomeTeamHeader = homeTeamHeader.slice(0, spreadIndex) + "(" + parseFloat(slider.value) + ")";
            var newAwayTeamHeader = awayTeamHeader.slice(0, awayTeamHeader.indexOf("(") - 1) + " (" + parseFloat(slider.value) + ")";
            
        } else {
            selectOptions[0].value = parseFloat(slider.value);
            selectOptions[1].value = "+" + parseFloat(slider.value);
            var newHomeTeamHeader = homeTeamHeader.slice(0, spreadIndex) + "(+" + parseFloat(slider.value) + ")";
            var newAwayTeamHeader = awayTeamHeader.slice(0, awayTeamHeader.indexOf("(") - 1) + " (" + parseFloat(slider.value) + ")";
            
        }
        document.getElementById("homeTeamHeader").innerHTML = newHomeTeamHeader;
        document.getElementById("awayTeamHeader").innerHTML = newAwayTeamHeader;
        spreadElement.innerHTML = selectOptions[selectedIndex].value;

    } else {
        if (slider.value > 0) {
            selectOptions[0].value = "+" + parseFloat(slider.value);
            selectOptions[1].value = "-" + parseFloat(slider.value);
            var newHomeTeamHeader = homeTeamHeader.slice(0, spreadIndex) + "(-" + parseFloat(slider.value) + ")";
            var newAwayTeamHeader = awayTeamHeader.slice(0, awayTeamHeader.indexOf("(") - 1) + " (+" + parseFloat(slider.value) + ")";

        } else if (slider.value === 0) {
            selectOptions[0].value = parseFloat(slider.value);
            selectOptions[1].value = parseFloat(slider.value);
            var newHomeTeamHeader = homeTeamHeader.slice(0, spreadIndex) + "(" + parseFloat(slider.value) + ")";
            var newAwayTeamHeader = awayTeamHeader.slice(0, awayTeamHeader.indexOf("(") - 1) + " (" + parseFloat(slider.value) + ")";
            
        } else {
            selectOptions[0].value = "+" + parseFloat(slider.value);
            selectOptions[1].value = parseFloat(slider.value);
            var newHomeTeamHeader = homeTeamHeader.slice(0, spreadIndex) + "(" + parseFloat(slider.value) + ")";
            var newAwayTeamHeader = awayTeamHeader.slice(0, awayTeamHeader.indexOf("(") - 1) + " (+" + parseFloat(slider.value) + ")";
            
        }       
        document.getElementById("homeTeamHeader").innerHTML = newHomeTeamHeader;
        document.getElementById("awayTeamHeader").innerHTML = newAwayTeamHeader;
        spreadElement.innerHTML = selectOptions[selectedIndex].value;
    }
}