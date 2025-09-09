import discord
from discord.ext import commands
import random
from utils.embeds import EmbedTemplates
from datetime import datetime

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_cooldowns = {}  # user_id: timestamp
        
    def calculate_level(self, xp):
        level = 0
        while xp >= (level + 1) * 100:
            xp -= (level + 1) * 100
            level += 1
        return level
    
    def calculate_total_xp_for_level(self, level):
        total_xp = 0
        for i in range(level):
            total_xp += (i + 1) * 100
        return total_xp
        
    async def get_leveling_settings(self, guild_id):
        """Get leveling settings for a guild"""
        try:
            result = await self.bot.db.fetchval(
                "SELECT leveling_enabled FROM leveling_settings WHERE guild_id = $1", guild_id
            )
            return result if result is not None else True  # Default enabled
        except Exception as e:
            print(f"Error getting leveling settings: {e}")
            return True  # Default enabled
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        # Check if leveling is enabled for this guild
        leveling_enabled = await self.get_leveling_settings(message.guild.id)
        if not leveling_enabled:
            return
            
        user_id = message.author.id
        guild_id = message.guild.id
        
        # Check cooldown (prevent spam)
        now = datetime.now().timestamp()
        if user_id in self.message_cooldowns:
            if now - self.message_cooldowns[user_id] < 60:  # 60 second cooldown
                return
                
        self.message_cooldowns[user_id] = now
        
        # Random XP gain (15-25 XP per message)
        xp_gain = random.randint(15, 25)
        
        try:
            # Get current stats
            current_data = await self.bot.db.fetchrow("""
                SELECT xp, level, messages FROM user_levels 
                WHERE user_id = $1 AND guild_id = $2
            """, user_id, guild_id)
            
            if current_data:
                new_xp = current_data['xp'] + xp_gain
                new_messages = current_data['messages'] + 1
                old_level = current_data['level']
            else:
                new_xp = xp_gain
                new_messages = 1
                old_level = 0
                
            new_level = self.calculate_level(new_xp)
            
            # Update database
            await self.bot.db.execute("""
                INSERT INTO user_levels (user_id, guild_id, xp, level, messages)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id, guild_id)
                DO UPDATE SET 
                    xp = $3,
                    level = $4,
                    messages = $5
            """, user_id, guild_id, new_xp, new_level, new_messages)
            
            # Check for level up
            if new_level > old_level:
                embed = EmbedTemplates.level_up(message.author, new_level, new_xp)
                await message.channel.send(embed=embed)
                
        except Exception as e:
            print(f"Error in leveling system: {e}")
            
    @commands.command(name='rank', aliases=['level', 'stats'])
    async def rank(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
            
        try:
            # Get user stats
            user_data = await self.bot.db.fetchrow("""
                SELECT xp, level, messages FROM user_levels 
                WHERE user_id = $1 AND guild_id = $2
            """, member.id, ctx.guild.id)
            
            if not user_data:
                if member == ctx.author:
                    embed = EmbedTemplates.info(
                        "No Stats Yet",
                        "Start chatting to gain XP and level up!",
                        ctx.author
                    )
                else:
                    embed = EmbedTemplates.info(
                        "No Stats Found",
                        f"{member.mention} hasn't gained any XP yet.",
                        ctx.author
                    )
                await ctx.send(embed=embed)
                return
                
            # Get user rank
            rank = await self.bot.db.fetchval("""
                SELECT COUNT(*) + 1 FROM user_levels 
                WHERE guild_id = $1 AND (
                    level > $2 OR 
                    (level = $2 AND xp > $3)
                )
            """, ctx.guild.id, user_data['level'], user_data['xp'])
            
            embed = EmbedTemplates.user_stats(
                member, 
                user_data['level'], 
                user_data['xp'], 
                user_data['messages'],
                rank
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedTemplates.error(
                "Error",
                f"Failed to fetch stats. Error: {str(e)}",
                ctx.author
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='leaderboard', aliases=['lb', 'top'])
    async def leaderboard(self, ctx):
        try:
            # Get top 10 users
            top_users = await self.bot.db.fetch("""
                SELECT user_id, xp, level, messages 
                FROM user_levels 
                WHERE guild_id = $1 
                ORDER BY level DESC, xp DESC 
                LIMIT 10
            """, ctx.guild.id)
            
            if not top_users:
                embed = EmbedTemplates.info(
                    "Empty Leaderboard",
                    "No one has gained XP yet! Start chatting to be first on the leaderboard!",
                    ctx.author
                )
                await ctx.send(embed=embed)
                return
                
            embed = discord.Embed(
                title="🏆 Server Leaderboard",
                description="Top 10 most active members",
                color=0xffd700,
                timestamp=datetime.now()
            )
            
            leaderboard_text = ""
            for i, user_data in enumerate(top_users, 1):
                user = self.bot.get_user(user_data['user_id'])
                if user:
                    name = user.display_name
                else:
                    name = f"Unknown User ({user_data['user_id']})"
                    
                if i == 1:
                    emoji = "🥇"
                elif i == 2:
                    emoji = "🥈"
                elif i == 3:
                    emoji = "🥉"
                else:
                    emoji = f"**{i}.**"
                    
                leaderboard_text += f"{emoji} **{name}**\n"
                leaderboard_text += f"     Level {user_data['level']} • {user_data['xp']:,} XP • {user_data['messages']:,} messages\n\n"
                
            embed.description = leaderboard_text
            
            # Find current user's rank
            user_rank = await self.bot.db.fetchval("""
                SELECT COUNT(*) + 1 FROM user_levels 
                WHERE guild_id = $1 AND user_id != $2 AND (
                    level > (SELECT COALESCE(level, 0) FROM user_levels WHERE user_id = $2 AND guild_id = $1) OR 
                    (level = (SELECT COALESCE(level, 0) FROM user_levels WHERE user_id = $2 AND guild_id = $1) 
                     AND xp > (SELECT COALESCE(xp, 0) FROM user_levels WHERE user_id = $2 AND guild_id = $1))
                )
            """, ctx.guild.id, ctx.author.id)
            
            embed.set_footer(text=f"{ctx.author.display_name}, you are ranked #{user_rank}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedTemplates.error(
                "Leaderboard Error",
                f"Failed to load leaderboard. Error: {str(e)}",
                ctx.author
            )
            await ctx.send(embed=embed)

    @rank.error
    async def rank_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = EmbedTemplates.error(
                "Invalid User",
                "Please provide a valid user.",
                ctx.author
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='leveling')
    @commands.has_permissions(manage_guild=True)
    async def toggle_leveling(self, ctx):
        """Toggle leveling system for this server"""
        try:
            current = await self.get_leveling_settings(ctx.guild.id)
            new_state = not current
            
            await self.bot.db.execute("""
                INSERT INTO leveling_settings (guild_id, leveling_enabled) VALUES ($1, $2)
                ON CONFLICT (guild_id) DO UPDATE SET leveling_enabled = $2
            """, ctx.guild.id, new_state)
            
            status = "enabled" if new_state else "disabled"
            embed = EmbedTemplates.success(
                "Leveling System Updated",
                f"Leveling system has been **{status}** for this server!",
                ctx.author
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedTemplates.error(
                "Database Error", 
                "Failed to update leveling settings.", 
                ctx.author
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))