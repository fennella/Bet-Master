from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json
from .models import FootballGame, PendingBet, MatchedBet
from accounts.models import CustomUser
from accounts.btcTasks import getBtcBalance
from .btcTasks import sendBtcToMaster
from django.db.models import Sum
import time
import math

class BetConsumer(WebsocketConsumer):

    def connect(self):
        
        self.betRoomNum = self.scope['url_route']['kwargs']['betRoomName']
        self.roomGroupName = 'betMaster_' + str(self.betRoomNum)

        # Join room group
        async_to_sync(self.channel_layer.group_add) (
            self.roomGroupName,
            self.channel_name
        )
        self.accept()
        
        game = FootballGame.objects.get(gameID=self.betRoomNum)
        bets = PendingBet.objects.filter(gameID=game.gameID).order_by('timestamp')
        pendingBets = []

        for bet in bets:
            betObj = {"id":bet.id, "pick":bet.pick, "amount":bet.amount, "offEven":bet.spreadOffEven, "address":bet.betterAddress}
            pendingBets.append(betObj)
        self.send(text_data=json.dumps({
            'command':'init',
            'message':{
                'homeTeam':game.homeTeam,
                'awayTeam':game.awayTeam,
                'homeTeamSpread':game.homeTeamSpread,
                'awayTeamSpread':game.awayTeamSpread,
                'evenSpread':game.evenSpread,
                'date': game.date,
                'time':game.time
            },
            'pendingBets': pendingBets
        }))

    def disconnect(self, close_code):
        # Leave room grouo
        async_to_sync(self.channel_layer.group_discard)(
            self.roomGroupName,
            self.channel_name
        )
    # Receive message from web socket
    def receive(self, text_data):

        textDataJSON = json.loads(text_data)
        betRequest = textDataJSON['betRequest']
        user = CustomUser.objects.get(username=betRequest['username'])
        btcBalance = getBtcBalance(user.btcKey)
        
        if float(btcBalance) != float(user.balance):
            user.balance = btcBalance
            user.save()

        ## Insufficient funds
        if float(btcBalance) < float(betRequest["amount"]):
            ## Handle not enough money in account
            print("Not enough money in account")
            self.send(text_data=json.dumps({
            # Send message back here
            'message':'Insufficient Funds'
            }))
            return 
        
        if betRequest['homeOrAway'] == "home":
            matchTeam = "away"
        else:
            matchTeam = "home"

            
        betSpreadChoice = float(betRequest['spread'])
        spreadRequest = float(betSpreadChoice * -1)
        aggSum = PendingBet.objects.filter(gameID=betRequest['gameID'], pick=matchTeam, spreadChoice=spreadRequest).aggregate(Sum('amount'))
        referringGame = FootballGame.objects.get(gameID=betRequest['gameID'])
        gameID = referringGame.gameID
        currentTime = time.time()
        spreadOffEven = (abs(float(betRequest['spread'])) - referringGame.evenSpread)

        ## Send bet amount to master for holding
        print(f'Sending {float(betRequest["amount"])} to master from {user.username}')
        sendBtcToMaster(user.btcKey, float(betRequest["amount"]))

        if aggSum['amount__sum'] is None:
            ## No match found, add to pending bets
            
            payout = round(float(betRequest['amount']) * 1.98, 10)
            
            print(f'Creating pending bet for {betRequest["username"]} for {betRequest["amount"]}')
            pendingBet = PendingBet(betterUsername=betRequest['username'],
                                    betterAddress=user.btcAddress,
                                    pick=betRequest['homeOrAway'],
                                    teamName=betRequest['teamName'],
                                    spreadChoice=betRequest['spread'],
                                    spreadOffEven=spreadOffEven,
                                    gameID=gameID,
                                    timestamp=currentTime,
                                    amount=betRequest['amount'],
                                    payout=payout)
            pendingBet.save()

            ## ACTUALLY SEND BITCOIN ##
            ## COMMNENT OUT FOR TESTING ##
            # print(f'Sending {round(float(betRequest["amount"]), 10)} to master from {user.username}')
            # sendBtcToMaster(user.btcKey, round(float(betRequest['amount']), 10))
            user.balance = float(user.balance) - round(float(betRequest['amount']), 10)
            user.save()
    
            betToSend = PendingBet.objects.get(timestamp=currentTime, betterUsername=betRequest['username'])
            betID = betToSend.id
            
            # Send message to room group
            async_to_sync(self.channel_layer.group_send)(
                self.roomGroupName,
                {
                    'type':'betMessage',
                    'command':"addBet",
                    'message': {
                        'pick':betRequest['homeOrAway'],
                        'btcAddress':user.btcAddress,
                        'amount':betRequest['amount'],
                        'offEven':spreadOffEven,
                        'newBalance':user.balance,
                        'id':betID
                    }
                }
            )
        else:
            ## Found potential bets to match
            betsToBeFilled = PendingBet.objects.filter(gameID=betRequest['gameID'], pick=matchTeam, spreadChoice=spreadRequest).order_by('timestamp')
            betRequestAmount = float(betRequest['amount'])
            
            for bet in betsToBeFilled:
                if betRequestAmount >= bet.amount:
                    ## Fulfill bet request
                    payout = round(float(betRequestAmount) * 1.98, 10)
                    print(f'Creating a matched bet between {user.username} and {bet.betterUsername} for {bet.amount}')
                    matchedBet = MatchedBet(better1=user.username, 
                                            better1Address=user.btcAddress, 
                                            better2=bet.betterUsername, 
                                            better2Address=bet.betterAddress, 
                                            better1Choice=betRequest['homeOrAway'], 
                                            better2Choice=bet.pick, 
                                            better1Spread=float(betRequest['spread']), 
                                            better2Spread=float(bet.spreadChoice), 
                                            better1TeamName=betRequest['teamName'], 
                                            better2TeamName=bet.teamName, 
                                            amount=bet.amount, 
                                            gameID=betRequest['gameID'], 
                                            payOutAmount=payout)
                    matchedBet.save()

                    # print(f'Matching a bet: Sending {bet.amount} btc to master from {user.username}')
                    # sendBtcToMaster(user.btcKey, bet.amount)

                    cleanNewBalance = round(user.balance - betRequestAmount, 10)
                    user.balance = cleanNewBalance
                    user.save()
                    
                    ## Remove table entry by bet ID
                    async_to_sync(self.channel_layer.group_send)(
                        self.roomGroupName,
                        {
                            'type':'betMessage',
                            'command':"deleteBet",
                            'message': {
                                'pick':bet.pick,
                                'offEven':bet.spreadOffEven,
                                'id':bet.id,
                                'better1':user.btcAddress,
                                'better2':bet.betterAddress,
                                'amount':betRequestAmount,
                                'newBalance':cleanNewBalance
                            }
                        }
                    )
                    betRequestAmount -= bet.amount
                    ## Delete pending bet matched with
                    bet.delete()

                
                elif betRequestAmount < float(bet.amount) and betRequestAmount > 0:
                    print("Filling partial amount")
                    ## Fill partial bet and break
                    outstandingBetAmount = round(bet.amount - betRequestAmount, 10)
                    payout = round(float(outstandingBetAmount) * 1.98, 10)
                    matchedBet = MatchedBet(better1=user.username, 
                                            better1Address=user.btcAddress, 
                                            better2=bet.betterUsername, 
                                            better2Address=bet.betterAddress, 
                                            better1Choice=betRequest['homeOrAway'], 
                                            better2Choice=bet.pick, 
                                            better1Spread=float(betRequest['spread']), 
                                            better2Spread=float(bet.spreadChoice), 
                                            better1TeamName=betRequest['teamName'], 
                                            better2TeamName=bet.teamName, 
                                            amount=betRequestAmount, 
                                            gameID=betRequest['gameID'], 
                                            payOutAmount=payout)
                    print(f'Creating matched bet between {user.username} and {bet.betterUsername} for {betRequestAmount}')
                    matchedBet.save()
                    ## Alert for partial matched bet

                    print(f'Updating pending bet amount from {bet.amount} to {outstandingBetAmount}')
                    bet.amount = outstandingBetAmount
                    bet.save()

                    # print(f'Filling partial amount: Sending {betRequestAmount} btc to master from {user.username}')
                    # sendBtcToMaster(user.btcKey, betRequestAmount)
                    newBtcBalance = user.balance - betRequestAmount
                    cleanNewBalance = round(user.balance - betRequestAmount, 10)
                    user.balance = newBtcBalance
                    user.save()

                    # Update table
                    async_to_sync(self.channel_layer.group_send)(
                        self.roomGroupName,
                        {
                            'type':'betMessage',
                            'command':"updateTable",
                            'message': {
                                'pick':bet.pick,
                                'offEven':bet.spreadOffEven,
                                'id':bet.id,
                                'newAmount':outstandingBetAmount,
                                'better1':user.btcAddress,
                                'better2':bet.betterAddress,
                                'amount':betRequestAmount,
                                'newBalance':cleanNewBalance
                            }
                        }
                    )
                    betRequestAmount = 0
                    
            if betRequestAmount > 0:
                print("Cleared all opposite bets, add entry")
                payout = round(float(betRequestAmount) * 1.98, 10)
                print(f'Creating pending bet for {betRequest["username"]} for {betRequestAmount}')
                pendingBet = PendingBet(betterUsername=betRequest['username'],betterAddress=user.btcAddress,pick=betRequest['homeOrAway'],teamName=betRequest['teamName'],spreadChoice=betRequest['spread'],spreadOffEven=spreadOffEven,gameID=gameID,timestamp=currentTime,amount=betRequestAmount,payout=payout)
                pendingBet.save()
                betToSend = PendingBet.objects.get(timestamp=currentTime, betterUsername=betRequest['username'])
                betID = betToSend.id
                remainder = round(float(betRequestAmount), 10)


                # print(f'Cleared all opposite bets: Sending {betRequestAmount} to master from {user.username}')
                # sendBtcToMaster(user.btcKey, betRequestAmount)

                async_to_sync(self.channel_layer.group_send)(
                    self.roomGroupName,
                    {
                        'type':'betMessage',
                        'command':"addBet",
                        'message': {
                            'pick':betRequest['homeOrAway'],
                            'btcAddress':user.btcAddress,
                            'amount':remainder,
                            'offEven':spreadOffEven,
                            'id':betID
                        }
                    }
                )
            

    
    # Receive message from room group
    def betMessage(self, event):
        
        message = event['message']
        command = event['command']
        
        print("Received a bet")

        # Send message to web socket
        self.send(text_data=json.dumps({
            'command':command,
            'message':message
        }))

        
