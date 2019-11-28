from django.contrib import admin
from .models import FootballGame, PendingBet, MatchedBet, CompleteBet
# Register your models here.
admin.site.register(FootballGame)
admin.site.register(PendingBet)
admin.site.register(MatchedBet)
admin.site.register(CompleteBet)