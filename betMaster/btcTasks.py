from bit import Key

MASTER_WALLET_ADDRESS = "1EJ1q6xo7mwVznVriEqUaUWzgEahK46fuW"
MASTER_WALLET_KEY = "KygMmH6PqZ6LSW7zFNB2kL1uoNzdQvyR3zrZuxF32XqoyHCw6QLK"

def sendBtcToMaster(userKey, amount):

    print("Trying a send to btc master")

    key = Key(userKey)

    transactions = [
        (MASTER_WALLET_ADDRESS, amount, 'btc')
    ]

    key.send(transactions)

def sendBtcToBetter(betterAddress, amount):

    print("Trying a send to better")
    
    key = Key(MASTER_WALLET_KEY)

    transactions = [
        (betterAddress, amount, 'btc')
    ]

    key.send(transactions)