from bit import Key

MASTER_WALLET_ADDRESS = "1EJ1q6xo7mwVznVriEqUaUWzgEahK46fuW"
MASTER_WALLET_KEY = "KygMmH6PqZ6LSW7zFNB2kL1uoNzdQvyR3zrZuxF32XqoyHCw6QLK"


def sendBtcToMaster(userKey, amount):

    key = Key(userKey)

    transactions = [
        (MASTER_WALLET_ADDRESS, amount, 'btc')
    ]

    key.send(transactions)

def sendBtcToBetter(betterAddress, amount):
    
    key = Key(MASTER_WALLET_KEY)

    transactions = [
        (betterAddress, amount, 'btc')
    ]

    key.send(transactions)