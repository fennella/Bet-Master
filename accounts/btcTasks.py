from pywallet import wallet
import qrcode
import base64
from io import BytesIO
from bit import Key
import requests

def makeWallet():
    # generate 12 word seed
    seed = wallet.generate_mnemonic()
    # create wallet
    btcWallet = wallet.create_wallet(network="BTC", seed=seed, children=0)

    return (btcWallet['address'], btcWallet['wif'].decode('ascii'))

def makeQRCode(address):

    buffered = BytesIO()
    img = qrcode.make(address)
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue())

def getBtcBalance(key):

    btcKey = Key(key)
    return btcKey.get_balance('btc')

def getBtcPrice():

    response = requests.get('http://api.coinmarketcap.com/v1/ticker/bitcoin')
    responseJSON = response.json()

    return float(responseJSON[0]['price_usd'])

def convertBTCtoUSD(btc):

    btcPrice = getBtcPrice()
    return "$" + str(round(btcPrice * btc, 2))





