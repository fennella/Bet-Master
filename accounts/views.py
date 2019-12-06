from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from .forms import CustomUserCreationForm, LoginForm
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib import messages
from .btcTasks import makeWallet, makeQRCode, getBtcPrice, getBtcBalance
from betMaster import oddsApiParse
import json


def index(request):

    return render(request, 'index.html', {'form':LoginForm})

def login_view(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)

            u = CustomUser.objects.get(username=username)
            btcBalance = getBtcBalance(u.btcKey)

            ## Set session variables    
            request.session['username'] = u.username
            request.session['btcAddress'] = u.btcAddress
            request.session['balance'] = btcBalance
            request.session['apiKey'] = u.apiKey
            request.session['conversionRate'] = getBtcPrice()
            qrBinary = u.qrCodeBinary
            request.session['qrCodeBinary'] = json.dumps(qrBinary.decode("utf-8"))

            ## Find, update and payout games that are not up to date
            oddsApiParse.findUpcomingGames()
            oddsApiParse.checkForCompletedGames()
            oddsApiParse.payoutCompletedGames()
            
            return redirect('betMaster/')
        else:
            return render(request, 'accounts/login.html', {'message': 'Invalid Login'})

    else:
        return render(request, 'accounts/login.html')

def register(request):

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            ## Create new user
            form.save()
            request.session['username'] = form.cleaned_data.get('username')
            username = form.cleaned_data.get('username')
            user = authenticate(username=username, password=form.cleaned_data.get('password'))
            
            ## Create bitcoin wallet
            address, key = makeWallet()
            ## Create QR Code
            qrBinary = makeQRCode(address)
            ## Update database 
            u = CustomUser.objects.get(username=username)
            u.btcAddress = address
            u.btcKey = key
            u.qrCodeBinary = qrBinary
            u.apiKey = abs(hash(address))
            u.save()
            
            ## Log user in
            login(request, user)

            ## Set session variables
            request.session['username'] = u.username
            request.session['btcAddress'] = u.btcAddress
            request.session['balance'] = u.balance
            request.session['apiKey'] = u.apiKey
            request.session['conversionRate'] = getBtcPrice()
            qrBinary = u.qrCodeBinary
            request.session['qrCodeBinary'] = json.dumps(qrBinary.decode("utf-8"))

            return redirect('betMaster/initProfile')
    else:

        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})




