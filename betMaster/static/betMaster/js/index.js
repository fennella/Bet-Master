function initPage(encodedImg, btcPrice, btcBalance) {
    console.log("From js script");
    var formattedString = encodedImg.replace(/&quot;/g, "");
    var imgSrc = 'data:image/png;base64,' + formattedString;
    var maxUSDWithdraw = (parseFloat(btcBalance) * parseFloat(btcPrice) - 1).toFixed(2);
    
    document.getElementById("maxUSDWithdraw").innerHTML = "Max Withdrawal: $" + String(maxUSDWithdraw);
    
    document.getElementById("qrCode").src = imgSrc;
    try {
        document.getElementById("initQRCodeImg").src = imgSrc;
    } catch(e) {
        // Not on initProfilePage
    }
    doPoll();
}

function doPoll(){
    $.get('updateBalance', function(data) {
        if (data !== "false") {
            document.getElementById("balanceNotifier").innerHTML = data;
            document.getElementById("balanceHeader").innerHTML = data;
        }
        setTimeout(doPoll,20000);
    });
}

function goToBetLobby(gameId) {

    window.location.pathname = '/betMaster/' + gameId + '/';
}

function showLive() {
    
    document.getElementById("liveDiv").style.display = "block";
    document.getElementById("upcomingDiv").style.display = "none";

    document.getElementById("upcomingHeader").style.textDecoration = "none";
    document.getElementById("liveHeader").style.textDecoration = "underline";
}

function showUpcoming() {
    
        document.getElementById("liveDiv").style.display = "none";
        document.getElementById("upcomingDiv").style.display = "block";

        document.getElementById("upcomingHeader").style.textDecoration = "underline";
        document.getElementById("liveHeader").style.textDecoration = "none";

}

function showWithdrawDiv() {
    console.log("Show withdraw div function");
    var divsToHide = document.getElementsByClassName("accountInfo");
    for (var i = 0; i < divsToHide.length; i++) {
        divsToHide[i].style.display = "none";
    }
    document.getElementById("withdrawDiv").style.display = "block";
}

function withdrawalRequest() {

    console.log("Withdrawal Function");

}

function showAccountInfo() {
    console.log("Showing account info function");
    var divsToShow = document.getElementsByClassName("accountInfo");
    for (var i = 0; i < divsToShow.length; i++) {
        divsToShow[i].style.display = "initial";
    }
    document.getElementById("withdrawDiv").style.display = "none";
}


function convertToBtc(rate) {
    
    var usdAmount = parseFloat(document.getElementById("usdWithdraw").value);
    var btcAmount = usdAmount / rate;
    btcAmount = btcAmount.toFixed(8);
    document.getElementById("btcWithdraw").value = btcAmount;
    var btcSendAddress = document.getElementById("btcWithdrawAddress").value;

    var maxBet = document.getElementById("maxUSDWithdraw").innerHTML;
    maxBet = parseFloat(maxBet.slice(17));
    
    if (usdAmount > maxBet) {
        console.log("Betting too much");
        document.getElementById("makeWithdrawBtn").disabled = true;
        document.getElementById("errorMessage").style.display = "block";
        document.getElementById("errorMessage").innerHTML = "Withdrawal Amount Exceeds Account Balance";
        document.getElementById("usdWithdraw").style.border = "2px solid red";
    } else {
        document.getElementById("errorMessage").style.display = "none";
        document.getElementById("usdWithdraw").style.border = "2px solid white";
        if (btcSendAddress.length > 25 && btcSendAddress.length < 37) {
            document.getElementById("makeWithdrawBtn").disabled = false;
        }
    }
    
    // if (usdAmount >= maxFloat) {
    //     console.log("Hitting error case");
    //     document.getElementById("placeBetBtn").disabled = true;
    //     document.getElementById("errorMessage").innerHTML = "Bet exceeds account balance";
    //     document.getElementById("errorMessage").style.display = "block";
    //     document.getElementById("usdInput").style.border = "2px solid red";

    // } else {
    //     console.log("Hitting valid case");
    //     document.getElementById("placeBetBtn").disabled = false;
    //     document.getElementById("errorMessage").style.display = "none";
    //     document.getElementById("usdInput").style.border = "2px solid white";
    // }
    // document.getElementById("usdPayout").value = usdString;
    // document.getElementById("btcPayout").value = btcPayout;

    

}