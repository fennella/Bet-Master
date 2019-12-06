from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from accounts.models import CustomUser
from accounts.btcTasks import getBtcBalance, getBtcPrice, convertBTCtoUSD
from . import oddsApiParse
from .models import FootballGame, PendingBet, MatchedBet, CompleteBet
import json
from django.db.models import Sum, Q
from django.utils.safestring import mark_safe
from websocket import create_connection
import pandas as pd

def index_view(request):

    updateMasterBalance()
    btcBalance = accessBtcBalance(request.session['username']) 

    ## Get data to populate home screen view
    upcomingGames = FootballGame.objects.filter(isLive=False, isComplete=False, awayTeamSpread__lt=999)

    largestBets = MatchedBet.objects.order_by('-amount')[:5]
    for bet in largestBets:
        bet.amount = f'{convertBTCtoUSD(bet.amount)}'
        bet.better1Spread = f'+-{abs(float(bet.better1Spread))}'

    return render(request, 'betMaster/index.html', {'btcBalance':btcBalance, 'upcomingGames':upcomingGames, 'largestBets':largestBets})

def initProfile_view(request):

    btcBalance = accessBtcBalance(request.session['username'])
    return render(request, 'betMaster/initProfile.html', {'btcBalance':btcBalance})

def updateBalance_view(request):

    username = request.session['username']

    u = CustomUser.objects.get(username=username)
    actualBtcBalance = getBtcBalance(u.btcKey)
    if float(actualBtcBalance) != float(u.balance):
        u.balance = actualBtcBalance
        u.save()
        request.session['balance'] = actualBtcBalance
        return HttpResponse(actualBtcBalance)
    
    return HttpResponse("false")
    
def accessBtcBalance(username):

    u = CustomUser.objects.get(username=username)
    return u.balance

def updateMasterBalance():

    u = CustomUser.objects.get(username="afennell")
    actualBtcBalance = getBtcBalance(u.btcKey)
    if float(actualBtcBalance) != float(u.balance):
        u.balance = actualBtcBalance
        u.save()

## Get data to init bet room 
def betRoom(request, betRoomName):
    gameDict = {}
    game = FootballGame.objects.get(gameID=int(betRoomName))

    gameDict['homeTeam'] = game.homeTeam
    gameDict['awayTeam'] = game.awayTeam
    gameDict['homeTeamSpread'] = game.homeTeamSpread
    gameDict['awayTeamSpread'] = game.awayTeamSpread
    gameDict['awayPicPath'] = game.awayTeamAbv + ".png"
    gameDict['homePicPath'] = game.homeTeamAbv + ".png"
    gameDict['evenSpread'] = game.evenSpread
 
    return render(request, 'betMaster/betRoom.html', {
        'betRoomNumJSON':mark_safe(json.dumps(betRoomName)), 'gameData':gameDict
    })

## API data request
def nflUpcomingView(request):

    try:
        apiKey = request.GET['API_KEY']
        if CustomUser.objects.filter(apiKey=apiKey).exists():
            upcomingGames = {"games":[]}
            for game in FootballGame.objects.filter(isLive=False, isComplete=False):
                if game.homeTeamSpread > 900 or game.awayTeamSpread > 900:
                    continue
                gameDict = {}
                gameDict = createHeaderData(gameDict, game)
                gameDict = createPendingData(gameDict, game)
                gameDict = createCompletedData(gameDict, game)
                gameDict = createPendingCompleteData(gameDict, game)

                upcomingGames['games'].append(gameDict)

            return HttpResponse(json.dumps(upcomingGames))
        
        else:
            # Invalid api key
            return HttpResponse("Invalid API Key")
    except:

        return HttpResponse("API Key Not Given. Please include your API Key as the API_KEY request parameter")

def createHeaderData(gameDict, game):

    gameDict['gameID'] = game.gameID
    gameDict['homeTeam'] = game.homeTeam
    gameDict['homeTeamAbv'] = game.homeTeamAbv
    gameDict['awayTeam'] = game.awayTeam
    gameDict['awayTeamAbv'] = game.awayTeamAbv
    gameDict['commenceTime'] = game.commenceTime

    gameDict['pendingBets'] = {}
    gameDict['completedBets'] = {}
    gameDict['pendingAndCompleted'] = {}
    
    return gameDict

def createPendingData(gameDict, game):

    pendingBets = PendingBet.objects.filter(gameID=game.gameID)

    pendingSum = pendingBets.aggregate(Sum('amount'))['amount__sum']
    if pendingSum is None:
        pendingSum = 0
    homePending = pendingBets.filter(pick='home')
    homeSum = homePending.aggregate(Sum('amount'))['amount__sum']
    if homeSum is None:
        homeSum = 0
    awayPending = pendingBets.filter(pick='away')
    awaySum = awayPending.aggregate(Sum('amount'))['amount__sum']
    if awaySum is None:
        awaySum = 0

    gameDict['pendingBets']['totalSum'] = pendingSum
    gameDict['pendingBets']['totalSumHome'] = homeSum
    gameDict['pendingBets']['totalSumAway'] = awaySum
    gameDict['pendingBets']['totalCount'] = pendingBets.count()
    gameDict['pendingBets']['totalCountHome'] = homePending.count()
    gameDict['pendingBets']['totalCountAway'] = awayPending.count()

    gameDict['pendingBets']['home'] = {}
    gameDict['pendingBets']['away'] = {}

    homeSpread = float(game.homeTeamSpread - 2)
    while homeSpread <= game.homeTeamSpread + 2:
        gameDict['pendingBets']['home'][homeSpread] = {}
        homeFilter = homePending.filter(spreadChoice=homeSpread)
        spreadSum = homeFilter.aggregate(Sum('amount'))['amount__sum']
        spreadCount = homeFilter.count()
        if spreadSum is None:
            spreadSum = 0
        gameDict['pendingBets']['home'][homeSpread]['amount'] = spreadSum
        gameDict['pendingBets']['home'][homeSpread]['count'] = spreadCount
        homeSpread += 0.5
    
    awaySpread = float(game.awayTeamSpread - 2)
    while awaySpread <= game.awayTeamSpread + 2:
        gameDict['pendingBets']['away'][awaySpread] = {}
        awayFilter = awayPending.filter(spreadChoice=awaySpread)
        spreadSum = awayFilter.aggregate(Sum('amount'))['amount__sum']
        spreadCount = awayFilter.count()
        if spreadSum is None:
            spreadSum = 0
        gameDict['pendingBets']['away'][awaySpread]['amount'] = spreadSum
        gameDict['pendingBets']['away'][awaySpread]['count'] = spreadCount
        awaySpread += 0.5
    
    return gameDict

def createCompletedData(gameDict, game):

    completedBets = MatchedBet.objects.filter(gameID=game.gameID)
    completeSum = completedBets.aggregate(Sum('amount'))['amount__sum']
    if completeSum is None:
        completeSum = 0
    completeCount = completedBets.count()

    gameDict['completedBets']['totalSum'] = completeSum * 2
    gameDict['completedBets']['homeSum'] = completeSum
    gameDict['completedBets']['awaySum'] = completeSum
    gameDict['completedBets']['totalCount'] = completeCount * 2
    gameDict['completedBets']['homeCount'] = completeCount
    gameDict['completedBets']['awayCount'] = completeCount

    gameDict['completedBets']['home'] = {}
    gameDict['completedBets']['away'] = {}

    homeSpread = float(game.homeTeamSpread - 2)
    while homeSpread <= game.homeTeamSpread + 2:
        gameDict['completedBets']['home'][homeSpread] = {}
        gameDict['completedBets']['away'][homeSpread * -1] = {}
        betsOnGame = completedBets.filter(Q(better1Spread=homeSpread) | Q(better1Spread=(homeSpread * -1)))
        gameSum = betsOnGame.aggregate(Sum('amount'))['amount__sum']
        gameCount = betsOnGame.count()
        if gameSum is None:
            gameSum = 0
        gameDict['completedBets']['home'][homeSpread]['amount'] = gameSum
        gameDict['completedBets']['home'][homeSpread]['count'] = gameCount
        gameDict['completedBets']['away'][homeSpread * -1]['amount'] = gameSum
        gameDict['completedBets']['away'][homeSpread * -1]['count'] = gameCount
        homeSpread += 0.5
    
    return gameDict

def createPendingCompleteData(gameDict, game):

    gameDict['pendingAndCompleted']['totalSum'] = gameDict['pendingBets']['totalSum'] + gameDict['completedBets']['totalSum']
    gameDict['pendingAndCompleted']['totalSumHome'] = gameDict['pendingBets']['totalSumHome'] + gameDict['completedBets']['homeSum']
    gameDict['pendingAndCompleted']['totalSumAway'] = gameDict['pendingBets']['totalSumAway'] + gameDict['completedBets']['awaySum']
    gameDict['pendingAndCompleted']['totalCount'] = gameDict['pendingBets']['totalCount'] + gameDict['completedBets']['totalCount']
    gameDict['pendingAndCompleted']['homeCount'] = gameDict['pendingBets']['totalCountHome'] + gameDict['completedBets']['homeCount']
    gameDict['pendingAndCompleted']['awayCount'] = gameDict['pendingBets']['totalCountAway'] + gameDict['completedBets']['awayCount']

    # Home pending/completed sum/totals
    gameDict['pendingAndCompleted']['home'] = {}
    for spread in gameDict['completedBets']['home'].keys():
        gameDict['pendingAndCompleted']['home'][spread] = {}
        gameDict['pendingAndCompleted']['home'][spread]['amount'] = gameDict['pendingBets']['home'][spread]['amount'] + gameDict['completedBets']['home'][spread]['amount']
        gameDict['pendingAndCompleted']['home'][spread]['count'] = gameDict['pendingBets']['home'][spread]['count'] + gameDict['completedBets']['home'][spread]['count']

    # Away pending/completed sum/totals
    gameDict['pendingAndCompleted']['away'] = {}
    for spread in gameDict['completedBets']['away'].keys():
        gameDict['pendingAndCompleted']['away'][spread] = {}
        gameDict['pendingAndCompleted']['away'][spread]['amount'] = gameDict['pendingBets']['away'][spread]['amount'] + gameDict['completedBets']['away'][spread]['amount']
        gameDict['pendingAndCompleted']['away'][spread]['count'] = gameDict['pendingBets']['away'][spread]['count'] + gameDict['completedBets']['away'][spread]['count']

    return gameDict

## API enpoint to place a bet
def nflPlaceBetView(request):

    try:

        apiKey = request.GET['API_KEY']
        gameID = request.GET['gameID']
        selection = request.GET['selection']
        spread = float(request.GET['spread'])
        amount = float(request.GET['amount'])
        if CustomUser.objects.filter(apiKey=apiKey).exists():
            user = CustomUser.objects.get(apiKey=apiKey)
            
            if FootballGame.objects.filter(gameID=gameID).exists():
                game = FootballGame.objects.get(gameID=gameID)

                if selection == "home":
                    homeEvenSpread = game.homeTeamSpread

                    if spread >= homeEvenSpread - 2 and spread <= homeEvenSpread + 2 and spread % 0.5 == 0:
                        validation = validateBetAmount(user.btcKey, amount)
                        if validation[0]:
                            btcPrice = validation[1]
                            connectToWebSocket(gameID, user, game, selection, spread, amount, btcPrice)
                            return HttpResponse(f'Bet of ${amount} successfully placed on the {game.homeTeam} at a spread of {spread}')
                        else:
                            return HttpResponse("Invalid amount specified. The amount should be in USD (ex: 30.50)")
                    else:
                        return HttpResponse("Invalid spread selection")

                elif selection == "away":
                    awayEvenSpread = game.awayTeamSpread
                    
                    if spread >= awayEvenSpread - 2 and spread <= awayEvenSpread + 2 and spread % 0.5 == 0:
                        validation = validateBetAmount(user.btcKey, amount)
                        if validation[0]:
                            btcPrice = validation[1]
                            connectToWebSocket(gameID, user, game, selection, spread, amount, btcPrice)
                            return HttpResponse(f'Bet of ${amount} successfully placed on the {game.awayTeam} at a spread of {spread}')

                        else:
                            return HttpResponse("Invalid amount specified. The amount should be in USD (ex: 30.50)")
                    else:
                        return HttpResponse("Invalid spread selection")

                else:

                    return HttpResponse("Invalid selection. Selection must be either 'home' or 'away'")
            
            else:

                return HttpResponse("Invalid game ID")

        else:
            # Invalid api key
            return HttpResponse("Invalid API Key")
    except:

        return HttpResponse("Not all parameters included in request. Please make sure API_KEY, gameID, selection, spread and amount parameters are included in request")

def validateBetAmount(key, amount):

    btcBalance = getBtcBalance(key)
    btcPrice = float(getBtcPrice())
    if (float(btcBalance) * btcPrice) - 0.5 >= amount:
        return (True, btcPrice)
    else:
        return False

def connectToWebSocket(gameID, user, game, selection, spread, amount, btcPrice):

    ws = create_connection('ws://localhost:8000/ws/betMaster/' + str(gameID) + '/')

    if selection == "home":
        teamName = game.homeTeam
    else:
        teamName = game.awayTeam

    btcBetAmount = round(amount / btcPrice, 8)

    betDict = {'betRequest':{}}
    betDict['betRequest']['username'] = user.username
    betDict['betRequest']['gameID'] = gameID
    betDict['betRequest']['homeOrAway'] = selection
    betDict['betRequest']['teamName'] = teamName
    betDict['betRequest']['spread'] = spread
    betDict['betRequest']['amount'] = btcBetAmount
    betDict['betRequest']['payout'] = round(btcBetAmount * 1.98, 8)

    jsonBetRequest = json.dumps(betDict)
    ws.send(jsonBetRequest)
    ws.recv()
    
## Get data for orders page
def ordersView(request):

    user = CustomUser.objects.get(username=request.session['username'])
    btcPrice = request.session['conversionRate']
    btcBalance = accessBtcBalance(user.username)

    allPending = PendingBet.objects.filter(betterUsername=user.username)
    allMatched = MatchedBet.objects.filter(Q(better1=user.username) | Q(better2=user.username))
    allComplete = CompleteBet.objects.filter(betterUsername=user.username)

    pendingOrders = generatePendingObjs(allPending)
    incompleteData = generateIncompleteObjs(allMatched, user)
    completeData = generateCompleteObjs(allComplete)
    performanceData = getProfitHistoryData(user, btcPrice)
    
    return render(request, 'betMaster/orders.html', {'btcBalance':btcBalance, 
                                                    'pendingOrders':pendingOrders, 
                                                    'incompleteBets':incompleteData, 
                                                    'completeBets':completeData,
                                                    'performanceData':performanceData})

def generatePendingObjs(allPending):

    pendingOrders = list(allPending.values('gameID', 'pick', 'spreadChoice', 'teamName').annotate(gameAmount=Sum('amount')))
    for pendOrder in pendingOrders:
        usdAmount = convertBTCtoUSD(pendOrder['gameAmount'])
        pendOrder['gameAmount'] = usdAmount
        referencingGame = FootballGame.objects.get(gameID=pendOrder['gameID'])
        pendOrder['gameSelection'] = f'{referencingGame.awayTeam} at {referencingGame.homeTeam}'
        pendOrder['date'] = referencingGame.date.strip()
        if float(pendOrder['spreadChoice']) > 0:
            pendOrder['spreadChoice'] = f'+{str(pendOrder["spreadChoice"])}'
    return pendingOrders

def generateIncompleteObjs(allMatched, user):

    incomplete = []
    for bet in allMatched:
        if bet.better1 == user.username:
            pick = bet.better1Choice
            spread = bet.better1Spread
            teamName = bet.better1TeamName
            ## Handle weird case of user being matched with self
            if bet.better1 == bet.better2:
                betObj2 = {'gameID':bet.gameID, 'pick':bet.better2Choice, 'spreadChoice':bet.better2Spread, 'amount':bet.amount, 'teamName':bet.better2TeamName}
                incomplete.append(betObj2)
        else:
            pick = bet.better2Choice
            spread = bet.better2Spread 
            teamName = bet.better2TeamName
        
        betObj = {'gameID':bet.gameID, 'pick':pick, 'spreadChoice':spread, 'amount': bet.amount, 'teamName':teamName}
        incomplete.append(betObj)


    incompleteData = []
    if len(incomplete) > 0:

        incompletePD = pd.DataFrame(incomplete).groupby(['gameID', 'pick', 'spreadChoice', 'teamName'])['amount'].sum()
        for row,amount in incompletePD.iteritems():

            referencingGame = FootballGame.objects.get(gameID=row[0])
            gameSelection = f'{referencingGame.awayTeam} at {referencingGame.homeTeam}'
            date = referencingGame.date

            if float(row[2]) > 0:
                spreadChoice = f'+{str(row[2])}'
            else:
                spreadChoice = str(row[2])
            
            usdAmount = convertBTCtoUSD(amount)
            incompleteData.append({'spreadChoice':spreadChoice, 'amount':usdAmount, 'teamName':row[3], 'gameSelection':gameSelection, 'date':date})

    incompleteData.reverse()

    return incompleteData

def generateCompleteObjs(allComplete):

    complete = []

    for bet in allComplete:
        teamName = bet.betterTeamName
        spread = bet.betterSpread
        amount = bet.amount
        didWin = bet.win
        payout = bet.payoutAmount
        gameID = bet.gameID

        complete.append({"gameID":gameID, "teamName":teamName, "spread":spread, "amount":amount, "didWin":didWin, "payout":payout})
    
    completeData = []
    if len(complete) > 0:

        completePD = pd.DataFrame(complete).groupby(['gameID', "spread", "teamName", "didWin"])['amount'].sum()
        print(completePD)

        for row,amount in completePD.iteritems():
            referencingGame = FootballGame.objects.get(gameID=row[0])
            gameSelection = f'{referencingGame.awayTeam} at {referencingGame.homeTeam}'
            date = referencingGame.date

            if float(row[1]) > 0:
                spreadChoice = f'+{str(row[1])}'
            else:
                spreadChoice = str(row[1])
            
            if row[3]:
                result = "Win"
                usdAmount = convertBTCtoUSD(amount)
            else:
                result = "Loss"
                usdAmount = convertBTCtoUSD(amount * -1)

            completeData.append({'spreadChoice':spreadChoice, 'payout':usdAmount, 'teamName':row[2], 'gameSelection':gameSelection, 'date':date, 'didWin':result})
    
    completeData.reverse()
    return completeData

def getProfitHistoryData(user, btcPrice):

    usersBets = CompleteBet.objects.filter(betterUsername=user.username)

    betHistoryDict = {}

    betHistoryDict['winPercHistory'] = {}
    betHistoryDict['profitHistory'] = {}
    betHistoryDict['totalBetAmount'] = ""
    betHistoryDict['totalLossAmount'] = ""
    betHistoryDict['totalBets'] = 0
    betHistoryDict['currProfit'] = ""
    betHistoryDict['totalWinAmount'] = ""

    wins = 0
    total = 1

    totalProfit = 0
    totalSpent = 0
    totalLost = 0
    totalWin = 0

    for bet in usersBets:

        if bet.win:
            wins += 1
            totalWin += round(bet.amount * 0.98, 8)
            totalProfit += round(bet.amount * 0.98, 8)
        else:
            totalLost += round(bet.amount, 8)
            totalProfit -= round(bet.amount, 8)

        betHistoryDict['profitHistory'][total] = round(btcPrice * totalProfit, 2)

        try:
            betHistoryDict['winPercHistory'][total] = round((wins / total) * 100, 2)
        except:
            betHistoryDict['winPercHistory'][total] = 0

        totalSpent += round(bet.amount, 8)
        total += 1
    try:

        betHistoryDict['currProfit'] = "$" + str(betHistoryDict['profitHistory'][len(betHistoryDict['profitHistory'])])
        betHistoryDict['totalBetAmount'] = "$" + str(round(totalSpent * btcPrice, 2))
        betHistoryDict['totalLossAmount'] = "$" + str(round(totalLost * btcPrice, 2))
        betHistoryDict['totalWinAmount'] = "$" + str(round(totalWin * btcPrice, 2))
        betHistoryDict['totalBets'] = total

    except:
        betHistoryDict['currProfit'] = "$0.00"
        betHistoryDict['totalBetAmount'] = "$0.00"
        betHistoryDict['totalLossAmount'] = "$0.00"
        betHistoryDict['totalWinAmount'] = "$0.00"
        betHistoryDict['totalBets'] = 0


    return betHistoryDict


