import discord
from discord.ext import commands
from utils.embeds import EmbedTemplates

class HelpMenu(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120.0)
        self.bot = bot
        
    @discord.ui.select(
        placeholder="Select a category...",
        options=[
            discord.SelectOption(
                label="General",
                description="General purpose commands.",
                emoji="💬"
            ),
            discord.SelectOption(
                label="Moderation", 
                description="Manage the server and its members.",
                emoji="🔨"
            ),
            discord.SelectOption(
                label="Leveling",
                description="View your stats and leaderboard.",
                emoji="📊"
            ),
            discord.SelectOption(
                label="Games",
                description="Play games with the bot or friends.",
                emoji="🎮"
            ),
            discord.SelectOption(
                label="Owner",
                description="Bot owner commands.",
                emoji="👑"
            ),
            discord.SelectOption(
                label="Show All",
                description="Display all commands at once.",
                emoji="📜"
            )
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = select.values[0]
        
        if category == "General":
            embed = discord.Embed(
                title="💬 General Commands",
                description="General purpose commands for everyone!",
                color=0x5865f2
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}help`",
                value="Display this help menu",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}ping`", 
                value="Check the bot's latency",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}info`",
                value="Display bot information",
                inline=False
            )
            
        elif category == "Moderation":
            embed = discord.Embed(
                title="🔨 Moderation Commands",
                description="Manage the server and its members.",
                color=0xff6b6b
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}kick <user> [reason]`",
                value="Kick a member from the server",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}ban <user> [reason]`",
                value="Ban a member from the server", 
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}warn <user> [reason]`",
                value="Warn a member",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}unwarn <user> <warning_id>`",
                value="Remove a warning from a member",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}warnings <user>`",
                value="View warnings for a member",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}automod`",
                value="Configure auto-moderation settings (spam, links, NSFW, warnings)",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}automod warnings`",
                value="Configure warning actions (auto-mute/kick/ban on warnings)",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}automod action <count> <action> [duration]`",
                value="Set automatic punishment for warning count (mute 5m, kick, ban)",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}welcome`",
                value="Configure welcome/leave messages (Admin only)",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}mute <user> [duration] [reason]`",
                value="Mute a member (5m, 2h, 1d format)",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}unmute <user> [reason]`",
                value="Unmute a member",
                inline=False
            )
            
        elif category == "Leveling":
            embed = discord.Embed(
                title="📊 Leveling Commands",
                description="View your stats and server leaderboard.",
                color=0x9b59b6
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}rank [user]`",
                value="View your or someone's level and stats",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}leaderboard`",
                value="View the server leaderboard",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}leveling`",
                value="Toggle leveling system on/off (Admin only)",
                inline=False
            )
            
        elif category == "Games":
            embed = discord.Embed(
                title="🎮 Games Commands",
                description="Play games with the bot or friends.",
                color=0xe74c3c
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}rps <choice>`",
                value="Play Rock Paper Scissors",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}guess <number>`",
                value="Guess a number between 1-100",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}8ball <question>`",
                value="Ask the magic 8-ball a question",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}coinflip`",
                value="Flip a coin",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}dice [sides]`",
                value="Roll a dice (default 6 sides)",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}trivia`",
                value="Answer trivia questions",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}wyr`",
                value="Get a Would You Rather question",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}flag`",
                value="Guess the country from its flag",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}blackjack`",
                value="Play a game of Blackjack (21)",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}slots`",
                value="Try your luck at the slot machine",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}tictactoe @user`",
                value="Play Tic Tac Toe against someone",
                inline=False
            )
            embed.add_field(
                name=f"`{await self.get_prefix(interaction)}challenge @user <game>`",
                value="Challenge someone to a game",
                inline=False
            )
            
        elif category == "Owner":
            embed = discord.Embed(
                title="👑 Owner Commands", 
                description="Commands only available to the bot owner.",
                color=0xffd700
            )
            embed.add_field(
                name="Owner Only",
                value="These commands are restricted to the bot owner for security.",
                inline=False
            )
            
        elif category == "Show All":
            embed = discord.Embed(
                title="📜 All Commands",
                description="Complete list of all available commands.",
                color=0x4ecdc4
            )
            embed.add_field(
                name="**💬 General**",
                value=f"`{await self.get_prefix(interaction)}help`, `{await self.get_prefix(interaction)}ping`, `{await self.get_prefix(interaction)}info`",
                inline=False
            )
            embed.add_field(
                name="**🔨 Moderation**", 
                value=f"`{await self.get_prefix(interaction)}kick`, `{await self.get_prefix(interaction)}ban`, `{await self.get_prefix(interaction)}warn`, `{await self.get_prefix(interaction)}unwarn`, `{await self.get_prefix(interaction)}warnings`, `{await self.get_prefix(interaction)}mute`, `{await self.get_prefix(interaction)}unmute`",
                inline=False
            )
            embed.add_field(
                name="**🛡️ Auto-Moderation**",
                value=f"`{await self.get_prefix(interaction)}automod`, `{await self.get_prefix(interaction)}automod spam`, `{await self.get_prefix(interaction)}automod links`, `{await self.get_prefix(interaction)}automod nsfw`, `{await self.get_prefix(interaction)}automod warnings`, `{await self.get_prefix(interaction)}automod action`",
                inline=False
            )
            embed.add_field(
                name="**🏠 Server Setup**",
                value=f"`{await self.get_prefix(interaction)}welcome`, `{await self.get_prefix(interaction)}leveling`",
                inline=False
            )
            embed.add_field(
                name="**📊 Leveling**",
                value=f"`{await self.get_prefix(interaction)}rank`, `{await self.get_prefix(interaction)}leaderboard`, `{await self.get_prefix(interaction)}leveling`",
                inline=False
            )
            embed.add_field(
                name="**🎮 Games**",
                value=f"`{await self.get_prefix(interaction)}rps`, `{await self.get_prefix(interaction)}guess`, `{await self.get_prefix(interaction)}8ball`, `{await self.get_prefix(interaction)}coinflip`, `{await self.get_prefix(interaction)}dice`, `{await self.get_prefix(interaction)}trivia`, `{await self.get_prefix(interaction)}wyr`, `{await self.get_prefix(interaction)}flag`, `{await self.get_prefix(interaction)}blackjack`, `{await self.get_prefix(interaction)}slots`, `{await self.get_prefix(interaction)}tictactoe`, `{await self.get_prefix(interaction)}challenge`",
                inline=False
            )
            embed.add_field(
                name="**⚙️ Settings**",
                value="`/prefix` - Change bot prefix (Slash Command)",
                inline=False
            )
            
        embed.set_footer(text="This menu will be active for 2 minutes.")
        await interaction.response.edit_message(embed=embed, view=self)
        
    async def get_prefix(self, interaction):
        guild_id = interaction.guild.id
        if guild_id in self.bot.prefixes:
            return self.bot.prefixes[guild_id]
        return '.'
        
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='help', aliases=['h', 'commands'])
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="🎮 Bot Help Menu",
            description="Select a category from the dropdown menu below to see its commands.",
            color=0x5865f2
        )
        
        embed.add_field(
            name="💬 General",
            value="General purpose commands.",
            inline=True
        )
        embed.add_field(
            name="🔨 Moderation", 
            value="Manage the server and its members.",
            inline=True
        )
        embed.add_field(
            name="📊 Leveling",
            value="View your stats and leaderboard.",
            inline=True
        )
        embed.add_field(
            name="🎮 Games",
            value="Play games with the bot or friends.",
            inline=True
        )
        embed.add_field(
            name="👑 Owner",
            value="Bot owner commands.",
            inline=True
        )
        embed.add_field(
            name="📜 Show All",
            value="Display all commands at once.",
            inline=True
        )
        
        embed.set_footer(text="This menu will be active for 2 minutes.")
        
        view = HelpMenu(self.bot)
        await ctx.send(embed=embed, view=view)
        
    @commands.command(name='ping')
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = EmbedTemplates.success(
            "Pong!",
            f"Bot latency: **{latency}ms**",
            ctx.author
        )
        await ctx.send(embed=embed)
        
    @commands.command(name='info', aliases=['about'])
    async def info(self, ctx):
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=0x5865f2
        )
        
        embed.add_field(name="🏷️ Version", value="v1.0.0", inline=True)
        embed.add_field(name="🐍 Python", value="3.11", inline=True)
        embed.add_field(name="📚 Discord.py", value="2.6.3", inline=True)
        embed.add_field(name="📊 Servers", value=f"{len(self.bot.guilds)}", inline=True)
        embed.add_field(name="👥 Users", value=f"{len(self.bot.users)}", inline=True)
        embed.add_field(name="⚙️ Prefix", value=f"`{await self.bot.get_prefix(ctx.message)}`", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))