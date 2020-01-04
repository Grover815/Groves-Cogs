from .call import KarmaOptions, asyncio

def setup(bot):
    n = KarmaOptions(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(n._check_bets())
    bot.add_cog(n)
