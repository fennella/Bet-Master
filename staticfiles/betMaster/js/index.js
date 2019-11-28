function initPage(encodedImg) {

    console.log("From js script");
    var formattedString = encodedImg.replace(/&quot;/g, "");
    var imgSrc = 'data:image/png;base64,' + formattedString;
    document.getElementById("qrCode").src = imgSrc;
    document.getElementById("initQRCodeImg").src = imgSrc;
}