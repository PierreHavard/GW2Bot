import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from .exceptions import APIError, APIKeyError


class WvwMixin:
    @commands.group()
    async def wvw(self, ctx):
        """Commands related to WVW"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @wvw.command(name="worlds")
    @commands.cooldown(1, 20, BucketType.user)
    async def wvw_worlds(self, ctx):
        """List all worlds"""
        try:
            results = await self.call_api("worlds?ids=all")
        except APIError as e:
            return await self.error_handler(ctx, e)
        output = "Available worlds are: ```"
        for world in results:
            output += world["name"] + ", "
        output += "```"
        await ctx.send(output)

    @wvw.command(name="info")
    @commands.cooldown(1, 10, BucketType.user)
    async def wvw_info(self, ctx, *, world: str=None):
        """Info about a world. If none is provided, defaults to account's world
        """
        user = ctx.author
        if not world:
            try:
                endpoint = "account"
                results = await self.call_api(endpoint, user)
                wid = results["world"]
            except APIKeyError as e:
                return await ctx.send(
                    "No world name or key associated with your account")
            except APIError as e:
                return await self.error_handler(ctx, e)
        else:
            wid = await self.get_world_id(world)
        if not wid:
            await ctx.send("Invalid world name")
            return
        try:
            endpoints = [
                "wvw/matches?world={0}".format(wid),
                "worlds?id={0}".format(wid)
            ]
            matches, worldinfo = await self.call_multiple(endpoints)
        except APIError as e:
            return await self.error_handler(ctx, e)
        for key, value in results["all_worlds"].items():
            if wid in value:
                worldcolor = key
        if not worldcolor:
            await ctx.send("Could not resolve world's color")
            return
        if worldcolor == "red":
            color = discord.Colour.red()
        elif worldcolor == "green":
            color = discord.Colour.green()
        else:
            color = discord.Colour.blue()
        score = results["scores"][worldcolor]
        ppt = 0
        victoryp = results["victory_points"][worldcolor]
        for m in results["maps"]:
            for objective in m["objectives"]:
                if objective["owner"].lower() == worldcolor:
                    ppt += objective["points_tick"]
        population = worldinfo["population"]
        if population == "VeryHigh":
            population = "Very high"
        kills = results["kills"][worldcolor]
        deaths = results["deaths"][worldcolor]
        kd = round((kills / deaths), 2)
        data = discord.Embed(description="Performance", colour=color)
        data.add_field(name="Score", value=score)
        data.add_field(name="Points per tick", value=ppt)
        data.add_field(name="Victory Points", value=victoryp)
        data.add_field(name="K/D ratio", value=str(kd), inline=False)
        data.add_field(name="Population", value=population, inline=False)
        data.set_author(name=worldinfo["name"])
        try:
            await ctx.send(embed=data)
        except discord.Forbidden:
            await ctx.send("Need permission to embed links")
