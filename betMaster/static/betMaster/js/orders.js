function deleteBet(betInfo) {

    var betInfoArr = betInfo.split(",")
    var spread = betInfoArr[0];
    var gameID = betInfoArr[1];

    $.ajax({

        url : 'deleteOrder',
        type : 'GET',
        data : {
            'spread': spread,
            'gameID': gameID
        },
        error : function(request,error) {
            console.log(error);
        }
        
    });
    
}