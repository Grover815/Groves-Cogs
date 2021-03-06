import discord
import asyncio
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

class KarmaOptions(commands.Cog):

    def __init__(self, bot:Red):
        self.bot = bot
        self.betsConf = Config.get_conf(self, identifier=betsID, force_registration=True)
        ReactKarma.karmaConf = Config.get_conf(karmaClass,identifier=karmaID, force_registration=True)
        ReactKarma.karmaConf.register_user(karma=0)
        ReactKarma.karmaConf.register_user(betKarma=0)
        self.betsConf.init_custom(BETS_GROUP, 2)
        self.betsConf.register_global(**{"codes":[]})

    ###				KarmaOptions functions			 ###

    @commands.group()
    async def bets(self, ctx: Context):
        """Check on bets
        """
        pass

    @bets.command(name="reset")
    @checks.is_owner()
    async def bets_reset(self, ctx: commands.Context, user: discord.User=None):
        """Reset bets group in config file
        """
        if user == None:
            await self.betsConf.clear_all()
            reply = "Reset bet configs."
            await ctx.send(reply)
        else:
            await ReactKarma.karmaConf.user(user).betKarma.set(0)
            reply = "Bet karma is now 0 for {}".format(user)
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
    			pred = bet[betCodes[x]]["pred"]
    			await ctx.send("```{0}: {1} bet {2} karma that {3} would pass {4} karma by {5}```".format(betCodes[x],authorName.name,bet[betCodes[x]]["loss"],userName.name,bet[betCodes[x]]["call"],pred.replace("00:00:00","")))
    	else:
    		await ctx.send("No active bets.")

    @bets.command(name="delete")
    @checks.is_owner()
    async def bets_delete(self,ctx:commands.Context, code):
        """Delete an active bet.

        Must use bet code found when bets are listed"""
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

    @commands.command(name="betboard")
    async def bet_board(self, ctx: commands.Context, top: int = 10):
        """Prints out the karma returns leaderboard.
        Defaults to top 10. Use negative numbers to reverse the leaderboard.
        """
        reverse = True
        if top == 0:
            top = 10
        elif top < 0:
            reverse = False
            top = -top
        members_sorted = sorted(
            await self._get_all_members(ctx.bot), key=lambda x: x.karma, reverse=reverse
        )
        if len(members_sorted) < top:
            top = len(members_sorted)
        topten = members_sorted[:top]
        highscore = ""
        place = 1
        for member in topten:
            highscore += str(place).ljust(len(str(top)) + 1)
            highscore += "{0} | ".format(member.name).ljust(18 - len(str(member.karma)))
            highscore += str(member.karma) + "\n"
            place += 1
        if highscore != "":
            embed = discord.Embed(color=0xf3f1f6)
            embed.title = "Karma Returns"
            embed.description = """```xl
{0}```""".format(highscore)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No one has gained or lost any karma")

    async def _check_bets(self):
        while self is self.bot.get_cog("KarmaOptions"):
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
        totalKarma = await settings.karma()
        betsKarma = await settings.betKarma()
        await settings.karma.set(totalKarma + int(amount))
        await settings.betKarma.set(betsKarma + int(amount))

    async def _remove_karma(self,user: discord.User, amount: int):
        settings = ReactKarma.karmaConf.user(user)
        totalKarma = await settings.karma()
        betsKarma = await settings.betKarma()
        await settings.karma.set(totalKarma - int(amount)) 
        await settings.betKarma.set(betsKarma - int(amount))  

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

    async def _gen_code(self):
    	taken_random = await self.betsConf.codes()
    	ranStr = await self._random_string()
    	if ranStr in taken_random:
    		await self._gen_code(self)
    	else:
    		global_group = self.betsConf
    		async with global_group.codes() as codes:
    				    codes.append(ranStr)
    		return ranStr

    async def _insert(self, ctx: commands.Context, user:discord.Member, call: int, date, bet: int, case):
        authorK = await ReactKarma.karmaConf.user(ctx.author).karma()
        if bet > authorK or bet <= 0:
            return 'Bet is too high'
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
               	    await self.betsConf.custom(BETS_GROUP).set_raw("{0}".format(await self._gen_code()),value = {'gain':gain, 'loss':bet, 'pred':str(pred),"author":ctx.author.id, "user": user.id, "call": call, "type": case})
               	    return "Success! May the odds be ever in your favor."

    async def _get_all_members(self, bot):
            """Get a list of members which have karma.
            Returns a list of named tuples with values for `name`, `id`, `karma`.
            """
            member_info = namedtuple("Member", "id name karma")
            ret = []
            for member in bot.get_all_members():
                if any(member.id == m.id for m in ret):
                    continue
                karma = await ReactKarma.karmaConf.user(member).betKarma()
                if karma == 0:
                    continue
                ret.append(member_info(id=member.id, name=str(member), karma=karma))
            return ret