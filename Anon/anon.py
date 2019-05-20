from redbot.core import commands, Config, checks
import discord
from discord.client import Client
import os


class Anon(commands.Cog):
    

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=81082083084)
        default ={
            "channelID":0,
            "serverID":0,
            "channelN":0,
            "serverN":0,
        }
        self.config.register_global(channelID=None,serverID=None,serverN=None,channelN=None)


    @commands.command()
    @checks.is_owner()
    async def share_off(self, ctx):
        """Disable Anon in the channel"""
        channel = ctx.message.channel
        curr = await self.config.channelID()
        if channel.id != curr:
            await ctx.send("Anon is already disabled")
        else:
            await self.config.channelID.set(None)
            await self.config.serverID.set(None)
            await self.config.channelN.set(None)
            await self.config.serverN.set(None)
            await ctx.send("Anon is disabled")


    @commands.command()
    @checks.is_owner()
    async def share_on(self, ctx):
        """Enable Anon in one channel"""
        channel = ctx.message.channel
        server = ctx.message.guild
        curr = await self.config.channelID()
        if channel.id == curr:
            await ctx.send("Anon already active")
        else:
            await self.config.channelID.set(channel.id)
            await self.config.serverID.set(server.id)
            await self.config.channelN.set(channel.name)
            await self.config.serverN.set(server.name)
            await ctx.send("Anon activated")


    @commands.command()
    async def post(self,ctx):
        """Post something wether it be a link,text, or image"""
        cont = ctx.message.content
        iids = float(int(await self.config.serverID()))
        iidc = float(int(await self.config.channelID()))
        server = self.bot.get_guild(iids)
        channel = self.bot.get_channel(iidc)
        if ctx.message.attachments != []:
            if ctx.message.attachments[0]. is_spoiler():
                await channel.send("||" + cont.replace(".post","") + "\n" + ctx.message.attachments[0].url + "||")
            else:
                await channel.send(cont.replace(".post","") + "\n" + ctx.message.attachments[0].url)
        else:
            await channel.send(cont.replace(".post", ""))


    @commands.command(pass_context=True)
    async def activec(self,ctx):
        """Check what channel Anon is active in"""
        try:
        	active = await self.config.channelID()
        	await ctx.send(active)
        except:
        	await ctx.send("No anon controlled channels")


    @commands.command(pass_context=True)
    async def actives(self,ctx):
        """Check what server Anon is active in"""
        try:
        	serv = await self.config.serverID()
        	await ctx.send(serv)
        except:
        	await ctx.send("No servers with anon active")


    async def build_embed(self, msg):
    	if msg.embeds != []:
    		embed = msg.embeds[0] 
    		em = discord.Embed(timestamp=msg.created_at)
    		if "title" in embed:
    			em.title = embed["title"]
    		if "description" in embed:
    			em.description = msg.clean_content + "\n\n" + embed["description"] + url
    		if "description" not in embed:
    			em.description = msg.clean_content
    		if "url" in embed:	
    			em.url = embed["url"]
    	else:
    		em = discord.Embed(timestamp=msg.created_at)
    		em.description = msg.content
    		if msg.attachments != []:
    			em.set_image(url=msg.attachments[0].url)
    		return em


def setup(bot):
	bot.add_cog(Anon(bot))

