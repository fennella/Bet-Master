from django.db import models
from django.contrib.auth.models import AbstractUser
from django import forms

class CustomUser(AbstractUser):

    balance = models.FloatField(default=0.0)
    btcAddress = models.CharField(max_length=200, null=True)
    btcKey = models.CharField(max_length=200, null=True)
    qrCodeBinary = models.BinaryField(max_length=None, null=True)
    apiKey = models.IntegerField(null=True)

    def __str__(self):
        return self.username

