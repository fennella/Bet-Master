from django.db import models

# Create your models here.
class FootballGame(models.Model):
    gameID = models.IntegerField(default=0)
    homeTeamAbv = models.CharField(max_length=20, null=True)
    homeTeam = models.CharField(max_length=200)
    homeTeamSpread = models.FloatField(max_length=5, default=999)
    awayTeam = models.CharField(max_length=200)
    awayTeamAbv = models.CharField(max_length=20, null=True)
    awayTeamSpread = models.FloatField(max_length=5, default=999)
    evenSpread = models.FloatField(max_length=5, default=999)
    commenceTime = models.IntegerField()
    homeTeamScore = models.IntegerField(default=0)
    awayTeamScore = models.IntegerField(default=0)
    date = models.CharField(max_length=20, null=True)
    time = models.CharField(max_length=20, null=True)
    isLive = models.BooleanField(default=False)
    isComplete = models.BooleanField(default=False)
    isPaidOut = models.BooleanField(default=False)


    def __str__(self):
        return f'{self.commenceTime} - {self.awayTeam} @ {self.homeTeam}' 

class PendingBet(models.Model):
    betterUsername = models.CharField(max_length=200)
    betterAddress = models.CharField(max_length=200, null=True)
    pick = models.CharField(max_length=200)
    teamName = models.CharField(max_length=200, null=True)
    spreadChoice = models.FloatField(null=True)
    spreadOffEven = models.FloatField(null=True)
    gameID = models.IntegerField()
    timestamp = models.IntegerField()
    amount = models.FloatField()
    payout = models.FloatField(null=True)

    def __str__(self):
        return f'{self.betterAddress} - {self.amount}'

class MatchedBet(models.Model):
    better1 = models.CharField(max_length=200)
    better1Address = models.CharField(max_length=200, null=True)
    better2 = models.CharField(max_length=200)
    better2Address = models.CharField(max_length=200, null=True)
    better1Choice = models.CharField(max_length=200, null=True)
    better2Choice = models.CharField(max_length=200, null=True)
    better1Spread = models.FloatField(null=True)
    better2Spread = models.FloatField(null=True)
    better1TeamName = models.CharField(max_length=200, null=True)
    better2TeamName = models.CharField(max_length=200, null=True)
    amount = models.FloatField(null=True)
    paidOut = models.BooleanField(default=False)
    gameID = models.IntegerField()
    payOutAmount = models.FloatField()

    def __str__(self):
        return f'{self.better1Address} vs {self.better2Address} - {self.amount}'

class CompleteBet(models.Model):
    betterUsername = models.CharField(max_length=200)
    betterAddress = models.CharField(max_length=200)
    betterChoice = models.CharField(max_length=20)
    betterTeamName = models.CharField(max_length=200)
    betterSpread = models.FloatField()
    amount = models.FloatField()
    win = models.BooleanField()
    gameID = models.IntegerField()
    payoutAmount = models.FloatField()

    def __str__(self):
        return f'{self.betterUsername} - {self.amount} - Win: {self.win}'


