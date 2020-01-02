import discord
import asyncio
from discord.client import Client
from collections import namedtuple
from redbot.core import commands, Config, checks
from redbot.core.commands import Context, Cog
from redbot.core.bot import Red
from datetime import datetime

from reactkarma import ReactKarma


betsID = 950481
date_format = "%m/%d/%Y"
BETS_GROUP = "BETS"


karmaID = 2617433287
karmaClass = ReactKarma()

class KarmaMarket(commands.Cog):

    def __init__(self, bot:Red):
        self.bot = bot
        self.betsConf = Config.get_conf(self, identifier=betsID, force_registration=True)
        ReactKarma.karmaConf = Config.get_conf(karmaClass,identifier=karmaID, force_registration=True)
        ReactKarma.karmaConf.register_user(karma=0)
        self.betsConf.init_custom(BETS_GROUP, 2)

    ###				KarmaMarket functions			 ###

    @commands.group()
    async def bets(self, ctx: Context):
        """Check on bets
        """
        pass

    @bets.command(name="reset")
    @checks.admin()
    async def bets_reset(self, ctx: commands.Context):
        await self.betsConf.custom(BETS_GROUP).clear()
        await ctx.send("Complete.")

    async def _check_bets(self):
        while self is self.bot.get_cog("KarmaMarket"):
            now = datetime.strptime(datetime.now().strftime(date_format), date_format)
            userBets = await self.betsConf.custom(BETS_GROUP).get_raw()
            for x in range(0,len(userBets)):
                if str(userBets[str(x)]["pred"]) == str(now):
                    await self._handle_bets(userBets[str(x)], x)
            await asyncio.sleep(3600) #   Check Every Hour

    async def _handle_bets(self, bet, index):
        userName =  self.bot.get_user(int(bet["user"]))
        userConf =  await ReactKarma.karmaConf.user(userName).get_raw()
        authorName = self.bot.get_user(int(bet["author"]))
        now = datetime.now()
        if now.hour == 23:
            await self._remove_karma(authorName,bet["loss"])
            await self.betsConf.custom(BETS_GROUP).clear_raw(index)
        else:
            if bet["type"] == "call":
                if userConf["karma"] >= bet["call"]:
                    await self._add_karma(authorName, bet["gain"])
                    await self.betsConf.custom(BETS_GROUP).clear_raw(index)
            elif bet["type"] == "put":
                if userConf["karma"] <= bet["call"]:
                    await self._add_karma(authorName, bet["gain"])
                    await self.betsConf.custom(BETS_GROUP).clear_raw(index)

    async def _add_karma(self, user: discord.User, amount: int):
        settings = ReactKarma.karmaConf.user(user)
        karma = await settings.karma()
        await settings.karma.set(karma + int(amount))
       
    async def _remove_karma(self,user: discord.User, amount: int):
        settings = ReactKarma.karmaConf.user(user)
        karma = await settings.karma()
        await settings.karma.set(karma - int(amount))        

    async def _what_is_options_return(self, karma, date, bet):
        a = karma*2/date
        b = bet/100
        return round(a*b)

    @commands.command()
    async def call(self, ctx: commands.Context, user:discord.Member, call: int, date, bet: int):
        """Bet on a users karma going up

        Call is the karma you think the user will pass
        Date is when you think they will pass it by
        """
        authorK = await ReactKarma.karmaConf.user(ctx.author).karma()
        if bet > authorK or bet <= 0:
            reply = 'Bet invalid.'
        else:
            now = datetime.strptime(datetime.now().strftime(date_format), date_format)
            pred = datetime.strptime(date, date_format)
            delta = pred - now
            diff_date = delta.days
            if diff_date <= 0:
                reply = "Predicted Date Invalid"
            else:
                curr_karma = await ReactKarma.karmaConf.user(user).karma()
                diff_karma = abs(call - curr_karma)
                gain = await self._what_is_options_return(diff_karma,diff_date,bet)
                curr_bet = await self.betsConf.custom(BETS_GROUP).get_raw()
                await self.betsConf.custom(BETS_GROUP).set_raw("{0}".format(len(curr_bet)),value = {'gain':gain, 'loss':bet, 'pred':str(pred),"author":ctx.author.id, "user": user.id, "call": call, "type": "call"})
                reply = "Success! Let the odds be ever in your favor."
        await ctx.send(reply)

    @commands.command()
    async def put(self, ctx: commands.Context, user:discord.Member, call: int, date, bet: int):
        """Bet on a users karma going down

        Call is the karma you think the user will pass
        Date is when you think they will pass it by
        """
        authorK = await ReactKarma.karmaConf.user(ctx.author).karma()
        if bet > authorK or bet <= 0:
            reply = 'Bet invalid.'
        else:
            now = datetime.strptime(datetime.now().strftime(date_format), date_format)
            pred = datetime.strptime(date, date_format)
            delta = pred - now
            diff_date = delta.days
            if diff_date <= 0:
                reply = "Predicted Date Invalid"
            else:
                curr_karma = await ReactKarma.karmaConf.user(user).karma()
                diff_karma = abs(call - curr_karma)
                gain = await self._what_is_options_return(diff_karma,diff_date,bet)
                curr_bet = await self.betsConf.custom(BETS_GROUP).get_raw()
                await self.betsConf.custom(BETS_GROUP).set_raw("{0}".format(len(curr_bet)),value = {'gain':gain, 'loss':bet, 'pred':str(pred),"author":ctx.author.id, "user": user.id, "call": call, "type": "put"})
                reply = "Success! Let the odds be ever in your favor."
        await ctx.send(reply)
