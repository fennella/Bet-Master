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

    print("Checking for all games within the next week")

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
    for game in data['games']:
        print("Found a game")
        gameID = game['schedule']['id']
        if FootballGame.objects.filter(gameID=gameID, awayTeamSpread=999).exists():
            print("Checking for spreads of this game")
            if not getGameSpreads(gameID):

                continue
            
            else:
                print("Updating an existing game object")
                game = FootballGame.objects.get(gameID=gameID)
                homeSpread, awaySpread = getGameSpreads(gameID)
                game.homeTeamSpread = homeSpread
                game.awayTeamSpread = awaySpread
                game.evenSpread = abs(homeSpread)
                game.save()

        elif not FootballGame.objects.filter(gameID=gameID).exists():

            print("Creating a new game object")
            dateText = game['schedule']['startTime']
            dateObj = dateutil.parser.parse(dateText)
            commenceTime = dateObj.timestamp()
            homeAbv = game['schedule']['homeTeam']['abbreviation']
            awayAbv = game['schedule']['awayTeam']['abbreviation']
            homeTeam = TEAMSDICT[homeAbv]
            awayTeam = TEAMSDICT[awayAbv]

            date, gameTime = formatTimeStamp(commenceTime)
            if not getGameSpreads(gameID):
                
                homeTeamSpread = 999
                awayTeamSpread = 999
                evenSpread = 999

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
        


def formatTimeStamp(timestamp):

    print(timestamp)
    estTimeStamp = timestamp - (60 * 60 * 5)
    dateObject = datetime.fromtimestamp(estTimeStamp)

    date = dateObject.strftime("%b %d")
    if int(dateObject.strftime("%H")) > 12:
        hour = int(dateObject.strftime("%H")) - 12
        time = f'{str(hour)}:{dateObject.strftime("%M")} PM'
    else:
        time = f'{dateObject.strftime("%H:%M")} AM'
    
    print(f'Time: {time}')
    print(f'Date: {date}')
    return (date, time)


def checkForCompletedGames():

    currentTimestamp = time.time()
    games = FootballGame.objects.filter(isComplete=False, commenceTime__lt=currentTimestamp)
    for game in games:
        print("Checking for a completed game here")
        print(game)
        for bet in PendingBet.objects.filter(gameID=game.gameID):
            ## Send bitcoin back to better
            print(f'Found a pending bet that did not get matched. Sending {bet.amount} btc to {bet.betterAddress}')
            sendBtcToBetter(bet.betterAddress, bet.amount)
            print('Sent btc back, now deleting pending bet object from DB')
            bet.delete()
        if game.commenceTime < currentTimestamp - (60 * 4):
            print("Found a game that started more than 4 hours ago...updating game object to complete")
            game.isComplete = True
            game.isLive = False
            game.save()
        else:
            print("Found a game that is currently in progress...updating game object to live")
            game.isLive = True
            game.save()

def payoutCompletedGames():

    print("Checking for completed games that have not been paid out yet")
    completedGames = FootballGame.objects.filter(isComplete=True, isPaidOut=False)
    for game in completedGames:
        print(f'Game that is complete and not paid out: {game}')
        betsOnGame = MatchedBet.objects.filter(paidOut=False, gameID=game.gameID)
        try:
            print("Getting game data")
            gameData = checkCompletedGameData(game.gameID)
        except:
            print("API sucks, getting game data failed...waiting for update")
            continue
        if gameData['game']['playedStatus'] == "COMPLETED":
            print(f'Found {game} to be a completed game that has not been paid out')
            print("Checking for matched bets on this game")
            if len(betsOnGame) > 0:
                print("Found at least 1 matched bet on this game")
                for bet in betsOnGame:
                    
                    print(f'In a matched bet for {game}')
                    print("Updating game object to input the score")
                    homeTeamScore = gameData['scoring']['homeScoreTotal']
                    awayTeamScore = gameData['scoring']['awayScoreTotal']
                    game.homeTeamScore = homeTeamScore
                    game.awayTeamScore = awayTeamScore
                    game.save()

                    winner = determineBetWinner(bet, homeTeamScore, awayTeamScore)
                    print(f'Found winner of {bet} to be {winner}')
                    
                    if winner is None:
                        print("Tie, sending bitcoin back")
                        sendBtcToBetter(bet.better1Address, bet.amount)
                        sendBtcToBetter(bet.better2Address, bet.amount)
                    else:
                        print("SENDING BITCOIN TO WINNER")
                        print(f'SENDING {bet.payOutAmount} TO {winner}')
                        sendBtcToBetter(winner, bet.payOutAmount)

                    createCompletedBets(winner, bet, game)

                    bet.delete()
            print("Game has been paid out, update game object to paid out")
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
