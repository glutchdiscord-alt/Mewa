import discord
from discord.ext import commands
from utils.embeds import EmbedTemplates
from datetime import datetime, timedelta
import re
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mute_check_task = None
        self.start_mute_checker()
    
    def parse_time(self, time_str):
        """Parse time string like '5m', '2h', '1d' into timedelta"""
        if not time_str:
            return None
            
        time_regex = re.match(r'^(\d+)([mhd])$', time_str.lower())
        if not time_regex:
            return None
            
        amount, unit = time_regex.groups()
        amount = int(amount)
        
        if unit == 'm':  # minutes
            return timedelta(minutes=amount)
        elif unit == 'h':  # hours
            return timedelta(hours=amount)
        elif unit == 'd':  # days
            return timedelta(days=amount)
        
        return None
    
    def start_mute_checker(self):
        """Start the background task to check for expired mutes"""
        if self.mute_check_task is None or self.mute_check_task.done():
            self.mute_check_task = asyncio.create_task(self.check_mutes())
    
    async def check_mutes(self):
        """Background task to unmute users when their mute expires"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                if self.bot.db:
                    # Get expired mutes
                    expired_mutes = await self.bot.db.fetch("""
                        SELECT user_id, guild_id, role_id 
                        FROM muted_users 
                        WHERE unmute_at <= $1
                    """, datetime.now())
                    
                    for mute in expired_mutes:
                        guild = self.bot.get_guild(mute['guild_id'])
                        if guild:
                            member = guild.get_member(mute['user_id'])
                            if member and mute['role_id']:
                                role = guild.get_role(mute['role_id'])
                                if role:
                                    try:
                                        await member.remove_roles(role)
                                    except:
                                        pass
                        
                        # Remove from database
                        await self.bot.db.execute("""
                            DELETE FROM muted_users 
                            WHERE user_id = $1 AND guild_id = $2
                        """, mute['user_id'], mute['guild_id'])
                        
            except Exception as e:
                print(f"Error in mute checker: {e}")
            
            await asyncio.sleep(60)  # Check every minute
        
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        if member == ctx.author:
            embed = EmbedTemplates.error(
                "Invalid Target",
                "You cannot kick yourself.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = EmbedTemplates.error(
                "Insufficient Permissions",
                "You cannot kick someone with a higher or equal role.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if member.top_role >= ctx.guild.me.top_role:
            embed = EmbedTemplates.error(
                "Bot Insufficient Permissions",
                "I cannot kick someone with a higher or equal role than me.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        try:
            # Send DM before kicking
            try:
                dm_embed = discord.Embed(
                    title="🔨 You have been kicked",
                    description=f"You were kicked from **{ctx.guild.name}**",
                    color=0xff6b6b
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled
                
            await member.kick(reason=reason)
            
            embed = EmbedTemplates.moderation("Kicked", member, ctx.author, reason)
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedTemplates.error(
                "Kick Failed",
                f"Failed to kick {member.mention}. Error: {str(e)}",
                ctx.author
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if member == ctx.author:
            embed = EmbedTemplates.error(
                "Invalid Target",
                "You cannot ban yourself.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = EmbedTemplates.error(
                "Insufficient Permissions",
                "You cannot ban someone with a higher or equal role.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if member.top_role >= ctx.guild.me.top_role:
            embed = EmbedTemplates.error(
                "Bot Insufficient Permissions",
                "I cannot ban someone with a higher or equal role than me.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        try:
            # Send DM before banning
            try:
                dm_embed = discord.Embed(
                    title="🔨 You have been banned",
                    description=f"You were banned from **{ctx.guild.name}**",
                    color=0xff6b6b
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled
                
            await member.ban(reason=reason, delete_message_days=0)
            
            embed = EmbedTemplates.moderation("Banned", member, ctx.author, reason)
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedTemplates.error(
                "Ban Failed",
                f"Failed to ban {member.mention}. Error: {str(e)}",
                ctx.author
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        if member == ctx.author:
            embed = EmbedTemplates.error(
                "Invalid Target",
                "You cannot warn yourself.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = EmbedTemplates.error(
                "Insufficient Permissions",
                "You cannot warn someone with a higher or equal role.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        try:
            # Add warning to database
            warning_id = await self.bot.db.fetchval("""
                INSERT INTO warnings (user_id, guild_id, moderator_id, reason)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, member.id, ctx.guild.id, ctx.author.id, reason or "No reason provided")
            
            # Get total warnings for user
            warning_count = await self.bot.db.fetchval("""
                SELECT COUNT(*) FROM warnings 
                WHERE user_id = $1 AND guild_id = $2
            """, member.id, ctx.guild.id)
            
            # Send DM to user
            try:
                dm_embed = discord.Embed(
                    title="⚠️ You have been warned",
                    description=f"You received a warning in **{ctx.guild.name}**",
                    color=0xffa726
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                dm_embed.add_field(name="Warning ID", value=f"#{warning_id}", inline=True)
                dm_embed.add_field(name="Total Warnings", value=f"{warning_count}", inline=True)
                await member.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled
                
            embed = discord.Embed(
                title="⚠️ Warning Issued",
                color=0xffa726,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Target", value=f"{member.mention} ({member})", inline=True)
            embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
            embed.add_field(name="Warning ID", value=f"#{warning_id}", inline=True)
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Total Warnings", value=f"{warning_count}", inline=True)
            
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedTemplates.error(
                "Warning Failed",
                f"Failed to warn {member.mention}. Error: {str(e)}",
                ctx.author
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason=None):
        """Mute a member with optional duration (5m, 2h, 1d)"""
        if member == ctx.author:
            embed = EmbedTemplates.error(
                "Invalid Target",
                "You cannot mute yourself.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = EmbedTemplates.error(
                "Insufficient Permissions",
                "You cannot mute someone with a higher or equal role.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
        
        # Get or create muted role
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            try:
                muted_role = await ctx.guild.create_role(
                    name="Muted",
                    color=discord.Color(0x818181),
                    reason="Auto-created muted role"
                )
                
                # Set up permissions for the muted role
                for channel in ctx.guild.channels:
                    try:
                        if isinstance(channel, discord.TextChannel):
                            await channel.set_permissions(muted_role, send_messages=False, add_reactions=False)
                        elif isinstance(channel, discord.VoiceChannel):
                            await channel.set_permissions(muted_role, speak=False, connect=False)
                    except:
                        continue
                        
            except Exception as e:
                embed = EmbedTemplates.error(
                    "Role Creation Failed",
                    f"Could not create muted role. Error: {str(e)}",
                    ctx.author
                )
                await ctx.send(embed=embed)
                return
        
        # Parse duration
        unmute_time = None
        duration_str = "Permanent"
        if duration:
            time_delta = self.parse_time(duration)
            if time_delta:
                unmute_time = datetime.now() + time_delta
                duration_str = duration
            else:
                embed = EmbedTemplates.error(
                    "Invalid Duration",
                    "Duration format should be like `5m`, `2h`, `1d` (m=minutes, h=hours, d=days)",
                    ctx.author
                )
                await ctx.send(embed=embed)
                return
        
        try:
            # Add muted role
            await member.add_roles(muted_role, reason=reason)
            
            # Store in database
            await self.bot.db.execute("""
                INSERT INTO muted_users (user_id, guild_id, role_id, muted_at, unmute_at, reason, moderator_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id, guild_id) DO UPDATE SET
                    role_id = $3, muted_at = $4, unmute_at = $5, reason = $6, moderator_id = $7
            """, member.id, ctx.guild.id, muted_role.id, datetime.now(), unmute_time, reason or "No reason provided", ctx.author.id)
            
            # Send DM to user
            try:
                dm_embed = discord.Embed(
                    title="🔇 You have been muted",
                    description=f"You were muted in **{ctx.guild.name}**",
                    color=0x818181
                )
                dm_embed.add_field(name="Duration", value=duration_str, inline=True)
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                if unmute_time:
                    dm_embed.add_field(name="Unmuted at", value=f"<t:{int(unmute_time.timestamp())}:f>", inline=False)
                await member.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled
                
            embed = discord.Embed(
                title="🔇 User Muted",
                color=0x818181,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Target", value=f"{member.mention} ({member})", inline=True)
            embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
            embed.add_field(name="Duration", value=duration_str, inline=True)
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            
            if unmute_time:
                embed.add_field(name="Unmuted at", value=f"<t:{int(unmute_time.timestamp())}:f>", inline=False)
            
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedTemplates.error(
                "Mute Failed",
                f"Failed to mute {member.mention}. Error: {str(e)}",
                ctx.author
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        """Unmute a member"""
        try:
            # Check if user is muted
            mute_data = await self.bot.db.fetchrow("""
                SELECT role_id FROM muted_users 
                WHERE user_id = $1 AND guild_id = $2
            """, member.id, ctx.guild.id)
            
            if not mute_data:
                embed = EmbedTemplates.error(
                    "User Not Muted",
                    f"{member.mention} is not currently muted.",
                    ctx.author
                )
                await ctx.send(embed=embed)
                return
            
            # Get muted role and remove it
            if mute_data['role_id']:
                role = ctx.guild.get_role(mute_data['role_id'])
                if role and role in member.roles:
                    await member.remove_roles(role, reason=reason)
            
            # Remove from database
            await self.bot.db.execute("""
                DELETE FROM muted_users 
                WHERE user_id = $1 AND guild_id = $2
            """, member.id, ctx.guild.id)
            
            # Send DM to user
            try:
                dm_embed = discord.Embed(
                    title="🔊 You have been unmuted",
                    description=f"You were unmuted in **{ctx.guild.name}**",
                    color=0x4ecdc4
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                await member.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled
                
            embed = discord.Embed(
                title="🔊 User Unmuted",
                description=f"{member.mention} has been unmuted",
                color=0x4ecdc4,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedTemplates.error(
                "Unmute Failed",
                f"Failed to unmute {member.mention}. Error: {str(e)}",
                ctx.author
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='unwarn')
    @commands.has_permissions(manage_messages=True) 
    async def unwarn(self, ctx, member: discord.Member, warning_id: int):
        try:
            # Check if warning exists and get details
            warning = await self.bot.db.fetchrow("""
                SELECT * FROM warnings 
                WHERE id = $1 AND user_id = $2 AND guild_id = $3
            """, warning_id, member.id, ctx.guild.id)
            
            if not warning:
                embed = EmbedTemplates.error(
                    "Warning Not Found",
                    f"Warning #{warning_id} not found for {member.mention}.",
                    ctx.author
                )
                await ctx.send(embed=embed)
                return
                
            # Remove warning
            await self.bot.db.execute("""
                DELETE FROM warnings 
                WHERE id = $1
            """, warning_id)
            
            embed = discord.Embed(
                title="✅ Warning Removed",
                description=f"Warning #{warning_id} has been removed from {member.mention}",
                color=0x4ecdc4,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Original Reason", value=warning['reason'], inline=False)
            embed.add_field(name="Removed by", value=ctx.author.mention, inline=True)
            
            embed.set_footer(text=f"User ID: {member.id}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedTemplates.error(
                "Unwarn Failed",
                f"Failed to remove warning. Error: {str(e)}",
                ctx.author
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='warnings')
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        try:
            warnings = await self.bot.db.fetch("""
                SELECT id, reason, moderator_id, timestamp 
                FROM warnings 
                WHERE user_id = $1 AND guild_id = $2
                ORDER BY timestamp DESC
            """, member.id, ctx.guild.id)
            
            if not warnings:
                embed = EmbedTemplates.info(
                    "No Warnings",
                    f"{member.mention} has no warnings.",
                    ctx.author
                )
                await ctx.send(embed=embed)
                return
                
            embed = discord.Embed(
                title=f"⚠️ Warnings for {member.display_name}",
                color=0xffa726,
                timestamp=datetime.now()
            )
            
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            
            for i, warning in enumerate(warnings[:10], 1):  # Show max 10 warnings
                moderator = self.bot.get_user(warning['moderator_id'])
                mod_name = moderator.display_name if moderator else "Unknown"
                
                embed.add_field(
                    name=f"Warning #{warning['id']}",
                    value=f"**Reason:** {warning['reason']}\n**Moderator:** {mod_name}\n**Date:** <t:{int(warning['timestamp'].timestamp())}:f>",
                    inline=False
                )
                
            if len(warnings) > 10:
                embed.set_footer(text=f"Showing 10 of {len(warnings)} warnings | User ID: {member.id}")
            else:
                embed.set_footer(text=f"Total warnings: {len(warnings)} | User ID: {member.id}")
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedTemplates.error(
                "Failed to Fetch Warnings",
                f"Could not retrieve warnings for {member.mention}. Error: {str(e)}",
                ctx.author
            )
            await ctx.send(embed=embed)

    # Error handlers
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = EmbedTemplates.error(
                "Missing Permissions",
                "You need `Kick Members` permission to use this command.",
                ctx.author
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = EmbedTemplates.error(
                "Invalid User",
                "Please provide a valid user to kick.",
                ctx.author
            )
            await ctx.send(embed=embed)

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = EmbedTemplates.error(
                "Missing Permissions", 
                "You need `Ban Members` permission to use this command.",
                ctx.author
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = EmbedTemplates.error(
                "Invalid User",
                "Please provide a valid user to ban.",
                ctx.author
            )
            await ctx.send(embed=embed)

    @warn.error
    @unwarn.error
    @warnings.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = EmbedTemplates.error(
                "Missing Permissions",
                "You need `Manage Messages` permission to use this command.",
                ctx.author
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = EmbedTemplates.error(
                "Invalid User",
                "Please provide a valid user.",
                ctx.author
            )
            await ctx.send(embed=embed)

    @mute.error
    @unmute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = EmbedTemplates.error(
                "Missing Permissions",
                "You need `Manage Roles` permission to use this command.",
                ctx.author
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = EmbedTemplates.error(
                "Invalid User",
                "Please provide a valid user.",
                ctx.author
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))