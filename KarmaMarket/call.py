import discord
import asyncio
from discord.client import Client
from collections import namedtuple
from redbot.core import commands, Config, checks
from redbot.core.commands import Context, Cog
from redbot.core.bot import Red
from datetime import datetime
import random
import string

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
        self.betsConf.register_global(**{"codes":[]})

    ###				KarmaMarket functions			 ###

    @commands.group()
    async def bets(self, ctx: Context):
        """Check on bets
        """
        pass

    @bets.command(name="reset")
    @checks.admin()
    async def bets_reset(self, ctx: commands.Context):
        """Reset bets group in config file
        """
        await self.betsConf.clear_all()
        reply = "Reset bet configs."
        await ctx.send(reply)

    @bets.command(name="list")
    async def bets_list(self, ctx:commands.Context):
    	"""List all active bets
    	"""
    	bet = await self.betsConf.custom(BETS_GROUP).get_raw()
    	betCodes = await self.betsConf.codes()
    	if len(betCodes) != 0:
    		for x in range(0,len(betCodes)):
    			userName =  self.bot.get_user(int(bet[betCodes[x]]["user"]))
    			authorName = self.bot.get_user(int(bet[betCodes[x]]["author"]))
    			await ctx.send("{0}: {1} bet {2} would reach {3} karma by {4}".format(betCodes[x],authorName,userName,bet[betCodes[x]]["call"],bet[betCodes[x]]["pred"]))
    	else:
    		await ctx.send("No active bets.")

    @bets.command(name="delete")
    async def bets_delete(self,ctx:commands.Context, code):
        """Delete an active bet.

        Must use bet code found when bets are lsited"""
        try:
            await self._delete_bet(code)
            await ctx.send("Bet {0} has been removed.".format(code))
        except:
            await ctx.send("No bet with code {0} found.".format(code))

    async def _delete_bet(self, code):
        global_group = self.betsConf
        async with global_group.codes() as codes:
            codes.remove(code)
        await self.betsConf.custom(BETS_GROUP).clear_raw(code)

    async def _check_bets(self):
        while self is self.bot.get_cog("KarmaMarket"):
            now = datetime.strptime(datetime.now().strftime(date_format), date_format)
            userBets = await self.betsConf.custom(BETS_GROUP).get_raw()
            betCodes = await self.betsConf.codes()
            for x in range(0,len(betCodes)):
                if str(userBets[betCodes[x]]["pred"]) == str(now):
                    await self._handle_bets(userBets[betCodes[x]], betCodes[x])
            await asyncio.sleep(3600) #   Check Every Hour

    async def _handle_bets(self, bet, code):
        userName =  self.bot.get_user(int(bet["user"]))
        userConf =  await ReactKarma.karmaConf.user(userName).get_raw()
        authorName = self.bot.get_user(int(bet["author"]))
        now = datetime.now()
        if now.hour == 23:
            await self._remove_karma(authorName,bet["loss"])
            await self._delete_bet(code)
        else:
            if bet["type"] == "call":
                if userConf["karma"] >= bet["call"]:
                    await self._add_karma(authorName, bet["gain"])
                    await self._delete_bet(code)
            elif bet["type"] == "put":
                if userConf["karma"] <= bet["call"]:
                    await self._add_karma(authorName, bet["gain"])
                    await self._delete_bet(code)

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

    async def _random_string(self,size=6, chars=string.ascii_uppercase + string.digits):
       return ''.join(random.choice(chars) for i in range(size))
       
    @commands.command()
    async def call(self, ctx: commands.Context, user:discord.Member, call: int, date, bet: int):
        """Bet on a users karma going up

        Call is the karma you think the user will pass
        Date is when you think they will pass it by
        """
        reply = await self._insert(ctx,user,call,date,bet,"call")
        await ctx.send(reply)

    @commands.command()
    async def put(self, ctx: commands.Context, user:discord.Member, call: int, date, bet: int):
        """Bet on a users karma going down

        Call is the karma you think the user will pass
        Date is when you think they will pass it by
        """
        reply = await self._insert(ctx,user,call,date,bet,"put")
        await ctx.send(reply)

    async def _gen_code(self,ctx):
    	taken_random = await self.betsConf.codes()
    	ranStr = await self._random_string()
    	if ranStr in taken_random:
    		await self._gen_code(self)
    	else:
    		taken_random_list = []
    		global_group = self.betsConf
    		async with global_group.codes() as codes:
    				    codes.append(ranStr)
    		return ranStr

    async def _insert(self, ctx: commands.Context, user:discord.Member, call: int, date, bet: int, case):
        authorK = await ReactKarma.karmaConf.user(ctx.author).karma()
        if bet > authorK or bet <= 0:
            return 'Bet invalid.'
        else:
            now = datetime.strptime(datetime.now().strftime(date_format), date_format)
            pred = datetime.strptime(date, date_format)
            delta = pred - now
            diff_date = delta.days
            if diff_date <= 0:
                return "Predicted Date Invalid"
            else:
                curr_karma = await ReactKarma.karmaConf.user(user).karma()
                diff_karma = abs(call - curr_karma)
                gain = await self._what_is_options_return(diff_karma,diff_date,bet)
                curr_bet = await self.betsConf.custom(BETS_GROUP).get_raw()
                if call < curr_karma and case == "call":
                    return "Called karma is lower than current karma. Try using a put instead"
                if call > curr_karma and case == "put":
                    return "Called karma is greater than current karma. Try using a call instead"
                else:
               	    await self.betsConf.custom(BETS_GROUP).set_raw("{0}".format(await self._gen_code(ctx)),value = {'gain':gain, 'loss':bet, 'pred':str(pred),"author":ctx.author.id, "user": user.id, "call": call, "type": case})
               	    return "Success! Let the odds be ever in your favor."
