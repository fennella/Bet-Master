import requests
import base64
import json
import time
import dateutil.parser
from .models import FootballGame, MatchedBet, PendingBet, CompleteBet
from .teamAbvMap import TEAMSDICT
from datetime import datetime, timezone
from .btcTasks import sendBtcToBetter

UNLIMITED_POSTGAME_KEY = "befcc0db-77b9-419a-838d-2b3666"


def findUpcomingGames():

    response = requests.get(
        url="https://api.mysportsfeeds.com/v2.1/pull/nfl/2019-regular/games.json",
        params={
            "date":"from-today-to-7-days-from-now"
        },
        headers={
            "Authorization": "Basic " + base64.b64encode('{}:{}'.format(UNLIMITED_POSTGAME_KEY,"MYSPORTSFEEDS").encode('utf-8')).decode('ascii')
        }
    )
    data = json.loads(response.content)
    ## Check games for actions to be taken
    for game in data['games']:
        gameID = game['schedule']['id']
        if FootballGame.objects.filter(gameID=gameID, awayTeamSpread=999).exists():
            ## Check spread for game
            if not getGameSpreads(gameID):

                continue
            
            else:
                ## Update an exisiting game object
                game = FootballGame.objects.get(gameID=gameID)
                homeSpread, awaySpread = getGameSpreads(gameID)
                game.homeTeamSpread = homeSpread
                game.awayTeamSpread = awaySpread
                game.evenSpread = abs(homeSpread)
                game.save()

        ## New game, does not exist in DB, create new game object
        elif not FootballGame.objects.filter(gameID=gameID).exists():

            dateText = game['schedule']['startTime']
            dateObj = dateutil.parser.parse(dateText)
            commenceTime = dateObj.timestamp()
            homeAbv = game['schedule']['homeTeam']['abbreviation']
            awayAbv = game['schedule']['awayTeam']['abbreviation']
            homeTeam = TEAMSDICT[homeAbv]
            awayTeam = TEAMSDICT[awayAbv]

            date, gameTime = formatTimeStamp(commenceTime)

            ## API has some games with no spread when game far in advance, set these
            ## game spreads to 999
            if not getGameSpreads(gameID):
                
                homeTeamSpread = 999
                awayTeamSpread = 999
                evenSpread = 999

            ## Found game spreads, get game spreads
            else:

                homeTeamSpread, awayTeamSpread = getGameSpreads(gameID)
                evenSpread = abs(homeTeamSpread)

            upcomingGame = FootballGame(gameID=gameID, 
                                        homeTeam=homeTeam, 
                                        homeTeamAbv=homeAbv, 
                                        homeTeamSpread=homeTeamSpread, 
                                        awayTeam=awayTeam, 
                                        awayTeamAbv=awayAbv, 
                                        awayTeamSpread=awayTeamSpread, 
                                        evenSpread=evenSpread, 
                                        commenceTime=commenceTime, 
                                        date=date, 
                                        time=gameTime)
            upcomingGame.save()
        
        

def getGameSpreads(gameID):
    response = requests.get(
        url="https://api.mysportsfeeds.com/v2.1/pull/nfl/current/odds_gamelines.json",
        params={
            "game":gameID
        },
        headers={
            "Authorization": "Basic " + base64.b64encode('{}:{}'.format(UNLIMITED_POSTGAME_KEY,"MYSPORTSFEEDS").encode('utf-8')).decode('ascii')
        }
    )
    data = json.loads(response.content)
    for game in data['gameLines']:
        try:
            awaySpread = game['lines'][0]['pointSpreads'][1]['pointSpread']['awaySpread']
            homeSpread = game['lines'][0]['pointSpreads'][1]['pointSpread']['homeSpread']
            return (homeSpread, awaySpread)
        except:
            return False
        

## Format timestamp to EST and readable date
def formatTimeStamp(timestamp):

    estTimeStamp = timestamp - (60 * 60 * 5)
    dateObject = datetime.fromtimestamp(estTimeStamp)

    date = dateObject.strftime("%b %d")
    if int(dateObject.strftime("%H")) > 12:
        hour = int(dateObject.strftime("%H")) - 12
        time = f'{str(hour)}:{dateObject.strftime("%M")} PM'
    else:
        time = f'{dateObject.strftime("%H:%M")} AM'
    
    return (date, time)

## Check to see if existing games in DB have completed
def checkForCompletedGames():

    currentTimestamp = time.time()
    games = FootballGame.objects.filter(isComplete=False, commenceTime__lt=currentTimestamp)
    for game in games:
        for bet in PendingBet.objects.filter(gameID=game.gameID):
            ## Found a game with pending bets
            ## Send bitcoin back to better
            sendBtcToBetter(bet.betterAddress, bet.amount)
            bet.delete()
        if game.commenceTime < currentTimestamp - (60 * 4):
            ## Update game status to complete if game started more than 4 hours ago
            game.isComplete = True
            game.isLive = False
            game.save()
        else:
            ## Game is currently in progress
            game.isLive = True
            game.save()

## Payout bets
def payoutCompletedGames():

    completedGames = FootballGame.objects.filter(isComplete=True, isPaidOut=False)
    for game in completedGames:
        ## Found game that is complete and not yet paid out
        betsOnGame = MatchedBet.objects.filter(paidOut=False, gameID=game.gameID)
        try:
            ## Get game data
            gameData = checkCompletedGameData(game.gameID)
        except:
            ## API not always reliable
            continue
        if gameData['game']['playedStatus'] == "COMPLETED":
            ## Check for matched bets on this game
            if len(betsOnGame) > 0:
                for bet in betsOnGame:
                    
                    ## Update score of game in DB
                    homeTeamScore = gameData['scoring']['homeScoreTotal']
                    awayTeamScore = gameData['scoring']['awayScoreTotal']
                    game.homeTeamScore = homeTeamScore
                    game.awayTeamScore = awayTeamScore
                    game.save()

                    winner = determineBetWinner(bet, homeTeamScore, awayTeamScore)
                    
                    ## There is a push, send bitcoin back
                    if winner is None:
                        sendBtcToBetter(bet.better1Address, bet.amount)
                        sendBtcToBetter(bet.better2Address, bet.amount)
                    ## Send bitcoin to winner
                    else:
                        sendBtcToBetter(winner, bet.payOutAmount)

                    createCompletedBets(winner, bet, game)

                    bet.delete()
            game.isPaidOut = True
            game.save()

def checkCompletedGameData(gameID):

    print("Checking for a completed game")

    response = requests.get(
        url="https://api.mysportsfeeds.com/v2.1/pull/nfl/current/games/" + str(gameID) + "/boxscore.json",
        headers={
            "Authorization": "Basic " + base64.b64encode('{}:{}'.format(UNLIMITED_POSTGAME_KEY,"MYSPORTSFEEDS").encode('utf-8')).decode('ascii')
        }
    )
    return json.loads(response.content)

def determineBetWinner(bet, homeTeamScore, awayTeamScore):

    if bet.better1Choice == "home":
        if homeTeamScore + bet.better1Spread > awayTeamScore:                            
            return bet.better1Address
        elif homeTeamScore + bet.better1Spread < awayTeamScore:                          
            return bet.better2Address
        else:
            return None
    else:
        if awayTeamScore + bet.better1Spread > homeTeamScore:
            return bet.better1Address
        elif awayTeamScore + bet.better1Spread < homeTeamScore:
            return bet.better2Address
        else:
            return None

def createCompletedBets(winner, bet, game):

    if bet.better1Address == winner:
        winnerCompleteBetObj = CompleteBet(betterUsername=bet.better1, 
                                    betterAddress=winner, 
                                    betterChoice=bet.better1Choice, 
                                    betterTeamName=bet.better1TeamName, 
                                    betterSpread=bet.better1Spread, 
                                    amount=bet.amount, 
                                    win=True,
                                    gameID=game.gameID,
                                    payoutAmount=bet.payOutAmount)
        winnerCompleteBetObj.save()
        loserCompleteBetObj = CompleteBet(betterUsername=bet.better2, 
                                    betterAddress=bet.better2Address, 
                                    betterChoice=bet.better2Choice, 
                                    betterTeamName=bet.better2TeamName, 
                                    betterSpread=bet.better2Spread, 
                                    amount=bet.amount, 
                                    win=False,
                                    gameID=game.gameID,
                                    payoutAmount=0)
        loserCompleteBetObj.save()
    else:
        winnerCompleteBetObj = CompleteBet(betterUsername=bet.better2, 
                                    betterAddress=winner, 
                                    betterChoice=bet.better2Choice, 
                                    betterTeamName=bet.better2TeamName, 
                                    betterSpread=bet.better2Spread, 
                                    amount=bet.amount, 
                                    win=True,
                                    gameID=game.gameID,
                                    payoutAmount=bet.payOutAmount)
        winnerCompleteBetObj.save()
        loserCompleteBetObj = CompleteBet(betterUsername=bet.better1, 
                                    betterAddress=bet.better1Address, 
                                    betterChoice=bet.better1Choice, 
                                    betterTeamName=bet.better1TeamName, 
                                    betterSpread=bet.better1Spread, 
                                    amount=bet.amount, 
                                    win=False,
                                    gameID=game.gameID,
                                    payoutAmount=0)
        loserCompleteBetObj.save()
