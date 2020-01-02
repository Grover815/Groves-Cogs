from .call import KarmaMarket
import asyncio

def setup(bot):
    n = KarmaMarket(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n._check_bets())
    bot.add_cog(n)
