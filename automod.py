import discord
from discord.ext import commands
import asyncio
import re
from collections import defaultdict, deque
from datetime import datetime, timedelta
from utils.embeds import EmbedTemplates

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = defaultdict(lambda: deque(maxlen=5))  # Track last 5 messages per user
        self.discord_link_pattern = re.compile(r'(https?://)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com/invite)/.+', re.IGNORECASE)
        
    async def get_automod_settings(self, guild_id):
        """Get automod settings for a guild"""
        try:
            async with self.bot.db.acquire() as conn:
                settings = await conn.fetchrow(
                    "SELECT * FROM automod_settings WHERE guild_id = $1", guild_id
                )
                if not settings:
                    # Create default settings
                    await conn.execute(
                        """INSERT INTO automod_settings (guild_id, warnings_enabled, discord_links_enabled, 
                           spam_enabled, spam_messages, spam_time, nsfw_enabled) VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                        guild_id, False, False, False, 5, 10, False
                    )
                    return {
                        'warnings_enabled': False,
                        'discord_links_enabled': False, 
                        'spam_enabled': False,
                        'spam_messages': 5,
                        'spam_time': 10,
                        'nsfw_enabled': False
                    }
                return dict(settings)
        except Exception as e:
            print(f"Error getting automod settings: {e}")
            return {
                'warnings_enabled': False,
                'discord_links_enabled': False,
                'spam_enabled': False, 
                'spam_messages': 5,
                'spam_time': 10,
                'nsfw_enabled': False
            }

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        settings = await self.get_automod_settings(message.guild.id)
        
        # Check spam
        if settings['spam_enabled']:
            await self.check_spam(message, settings)
            
        # Check discord links
        if settings['discord_links_enabled']:
            await self.check_discord_links(message)
            
        # Check NSFW content
        if settings.get('nsfw_enabled', False):
            await self.check_nsfw_content(message, settings)
    
    async def check_spam(self, message, settings):
        """Check for spam messages"""
        user_id = message.author.id
        now = datetime.now()
        
        # Add current message to tracker
        self.spam_tracker[user_id].append(now)
        
        # Check if user sent too many messages in time window
        recent_messages = [
            msg_time for msg_time in self.spam_tracker[user_id]
            if now - msg_time <= timedelta(seconds=settings['spam_time'])
        ]
        
        if len(recent_messages) >= settings['spam_messages']:
            try:
                # Delete the spam messages
                await message.delete()
                
                # Issue warning
                if settings['warnings_enabled']:
                    await self.add_warning(message.author, message.guild, "Spam detection")
                
                # Send warning message
                embed = EmbedTemplates.warning(
                    "Spam Detected",
                    f"{message.author.mention} slow down! You're sending messages too quickly.",
                    message.author
                )
                warning_msg = await message.channel.send(embed=embed)
                
                # Delete warning after 5 seconds
                await asyncio.sleep(5)
                try:
                    await warning_msg.delete()
                except:
                    pass
                    
                # Clear spam tracker for user
                self.spam_tracker[user_id].clear()
                
            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"Error handling spam: {e}")
    
    async def check_discord_links(self, message):
        """Check for Discord invite links"""
        if self.discord_link_pattern.search(message.content):
            try:
                await message.delete()
                
                embed = EmbedTemplates.warning(
                    "Discord Link Removed",
                    f"{message.author.mention} Discord invite links are not allowed!",
                    message.author
                )
                warning_msg = await message.channel.send(embed=embed)
                
                # Delete warning after 5 seconds
                await asyncio.sleep(5)
                try:
                    await warning_msg.delete()
                except:
                    pass
                    
            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"Error handling discord link: {e}")
    
    async def check_nsfw_content(self, message, settings):
        """Check for NSFW content"""
        # NSFW keywords to filter
        nsfw_keywords = [
            'sex', 'porn', 'nsfw', 'nude', 'naked', 'xxx', 'adult', 'erotic',
            'sexual', 'penis', 'vagina', 'breast', 'boob', 'tit', 'ass', 'dick', 
            'cock', 'pussy', 'fuck', 'shit', 'bitch', 'damn', 'orgasm', 
            'masturbat', 'horny', 'aroused', 'kinky', 'fetish'
        ]
        
        content_lower = message.content.lower()
        is_nsfw = False
        
        # Check message content for NSFW keywords
        for keyword in nsfw_keywords:
            if keyword in content_lower:
                is_nsfw = True
                break
        
        # Check attachment filenames
        if not is_nsfw and message.attachments:
            for attachment in message.attachments:
                filename_lower = attachment.filename.lower()
                for keyword in nsfw_keywords:
                    if keyword in filename_lower:
                        is_nsfw = True
                        break
                if is_nsfw:
                    break
        
        if is_nsfw:
            try:
                # Delete the NSFW message
                await message.delete()
                
                # Issue warning if enabled
                if settings['warnings_enabled']:
                    await self.add_warning(message.author, message.guild, "NSFW content detection")
                
                # Send warning message
                embed = EmbedTemplates.warning(
                    "NSFW Content Removed",
                    f"{message.author.mention} inappropriate content is not allowed in this server!",
                    message.author
                )
                warning_msg = await message.channel.send(embed=embed)
                
                # Delete warning after 5 seconds
                await asyncio.sleep(5)
                try:
                    await warning_msg.delete()
                except:
                    pass
                    
            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"Error handling NSFW content: {e}")
    
    async def add_warning(self, user, guild, reason):
        """Add a warning to the database and execute warning actions"""
        try:
            async with self.bot.db.acquire() as conn:
                await conn.execute(
                    """INSERT INTO warnings (guild_id, user_id, reason, moderator_id, warned_at)
                       VALUES ($1, $2, $3, $4, $5)""",
                    guild.id, user.id, reason, self.bot.user.id, datetime.now()
                )
                
                # Get total warnings for user
                warning_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM warnings 
                    WHERE user_id = $1 AND guild_id = $2
                """, user.id, guild.id)
                
                # Check for warning actions
                action = await conn.fetchrow("""
                    SELECT action_type, duration FROM warning_actions 
                    WHERE guild_id = $1 AND warning_count = $2
                """, guild.id, warning_count)
                
                if action:
                    await self.execute_warning_action(user, guild, action, warning_count)
                    
        except Exception as e:
            print(f"Error adding warning: {e}")
    
    async def execute_warning_action(self, user, guild, action, warning_count):
        """Execute the configured action for reaching warning threshold"""
        try:
            action_type = action['action_type']
            duration = action['duration']
            
            if action_type == 'mute':
                # Get moderation cog to use mute functionality
                mod_cog = self.bot.get_cog('Moderation')
                if mod_cog:
                    # Get or create muted role
                    muted_role = discord.utils.get(guild.roles, name="Muted")
                    if not muted_role:
                        muted_role = await guild.create_role(
                            name="Muted",
                            color=discord.Color(0x818181),
                            reason="Auto-created for warning actions"
                        )
                        
                        # Set up permissions for the muted role
                        for channel in guild.channels:
                            try:
                                if isinstance(channel, discord.TextChannel):
                                    await channel.set_permissions(muted_role, send_messages=False, add_reactions=False)
                                elif isinstance(channel, discord.VoiceChannel):
                                    await channel.set_permissions(muted_role, speak=False, connect=False)
                            except:
                                continue
                    
                    member = guild.get_member(user.id)
                    if member:
                        # Parse duration and calculate unmute time
                        unmute_time = None
                        if duration and duration != 'permanent':
                            time_delta = mod_cog.parse_time(duration)
                            if time_delta:
                                unmute_time = datetime.now() + time_delta
                        
                        # Add muted role
                        await member.add_roles(muted_role, reason=f"Auto-mute: {warning_count} warnings")
                        
                        # Store in database
                        await self.bot.db.execute("""
                            INSERT INTO muted_users (user_id, guild_id, role_id, muted_at, unmute_at, reason, moderator_id)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            ON CONFLICT (user_id, guild_id) DO UPDATE SET
                                role_id = $3, muted_at = $4, unmute_at = $5, reason = $6, moderator_id = $7
                        """, member.id, guild.id, muted_role.id, datetime.now(), unmute_time, 
                             f"Auto-mute: {warning_count} warnings", self.bot.user.id)
                        
            elif action_type == 'kick':
                member = guild.get_member(user.id)
                if member:
                    await member.kick(reason=f"Auto-kick: {warning_count} warnings")
                    
            elif action_type == 'ban':
                member = guild.get_member(user.id)
                if member:
                    await member.ban(reason=f"Auto-ban: {warning_count} warnings", delete_message_days=0)
                    
        except Exception as e:
            print(f"Error executing warning action: {e}")
    
    @commands.group(name='automod', invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def automod(self, ctx):
        """Auto-moderation settings"""
        settings = await self.get_automod_settings(ctx.guild.id)
        
        embed = discord.Embed(
            title="🛡️ Auto-Moderation Settings",
            color=0x5865f2
        )
        
        embed.add_field(
            name="📝 Auto Warnings",
            value="✅ Enabled" if settings['warnings_enabled'] else "❌ Disabled",
            inline=True
        )
        embed.add_field(
            name="🔗 Discord Links",
            value="✅ Enabled" if settings['discord_links_enabled'] else "❌ Disabled", 
            inline=True
        )
        embed.add_field(
            name="💬 Spam Detection",
            value="✅ Enabled" if settings['spam_enabled'] else "❌ Disabled",
            inline=True
        )
        embed.add_field(
            name="🔞 NSFW Filter",
            value="✅ Enabled" if settings.get('nsfw_enabled', False) else "❌ Disabled",
            inline=True
        )
        
        if settings['spam_enabled']:
            embed.add_field(
                name="⚙️ Spam Settings",
                value=f"**Messages:** {settings['spam_messages']}\n**Time:** {settings['spam_time']}s",
                inline=False
            )
        
        prefix = await self.bot.get_prefix(ctx.message)
        if isinstance(prefix, list):
            prefix = prefix[0]
            
        embed.add_field(
            name="🔧 Commands",
            value=f"`{prefix}automod warnings` - Toggle auto warnings\n"
                  f"`{prefix}automod links` - Toggle Discord link blocking\n"
                  f"`{prefix}automod spam` - Toggle spam detection\n"
                  f"`{prefix}automod spam-config <messages> <seconds>` - Configure spam settings",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)
    
    @automod.command(name='warnings')
    @commands.has_permissions(manage_guild=True)
    async def configure_warnings(self, ctx, action: str = None):
        """Configure auto warnings and warning actions"""
        if action == "toggle":
            try:
                async with self.bot.db.acquire() as conn:
                    current = await conn.fetchval(
                        "SELECT warnings_enabled FROM automod_settings WHERE guild_id = $1", ctx.guild.id
                    )
                    new_state = not current if current is not None else True
                    
                    await conn.execute(
                        """INSERT INTO automod_settings (guild_id, warnings_enabled) VALUES ($1, $2)
                           ON CONFLICT (guild_id) DO UPDATE SET warnings_enabled = $2""",
                        ctx.guild.id, new_state
                    )
                    
                    status = "enabled" if new_state else "disabled"
                    embed = EmbedTemplates.success(
                        "Auto Warnings Updated",
                        f"Auto warnings have been **{status}**!",
                        ctx.author
                    )
                    await ctx.send(embed=embed)
                    
            except Exception as e:
                embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
                await ctx.send(embed=embed)
        else:
            # Show warning actions configuration menu
            try:
                async with self.bot.db.acquire() as conn:
                    actions = await conn.fetch("""
                        SELECT warning_count, action_type, duration 
                        FROM warning_actions 
                        WHERE guild_id = $1 
                        ORDER BY warning_count
                    """, ctx.guild.id)
                    
                    embed = discord.Embed(
                        title="⚠️ Warning Actions Configuration",
                        description="Configure what happens when users reach certain warning counts.",
                        color=0xffa726
                    )
                    
                    if actions:
                        actions_text = ""
                        for action in actions:
                            duration_text = f" ({action['duration']})" if action['duration'] and action['duration'] != 'permanent' else ""
                            actions_text += f"**{action['warning_count']} warnings** → {action['action_type'].title()}{duration_text}\n"
                        embed.add_field(name="Current Actions", value=actions_text, inline=False)
                    else:
                        embed.add_field(name="Current Actions", value="No warning actions configured", inline=False)
                    
                    prefix = await self.bot.get_prefix(ctx.message)
                    if isinstance(prefix, list):
                        prefix = prefix[0]
                    
                    embed.add_field(
                        name="🔧 Commands",
                        value=f"`{prefix}automod warnings toggle` - Toggle auto warnings on/off\n"
                              f"`{prefix}automod action <warnings> <action> [duration]` - Set warning action\n"
                              f"`{prefix}automod remove-action <warnings>` - Remove warning action\n\n"
                              f"**Actions:** mute, kick, ban\n"
                              f"**Duration format:** 5m, 2h, 1d (for mute only)",
                        inline=False
                    )
                    
                    await ctx.send(embed=embed)
                    
            except Exception as e:
                embed = EmbedTemplates.error("Database Error", "Failed to load settings.", ctx.author)
                await ctx.send(embed=embed)
    
    @automod.command(name='action')
    @commands.has_permissions(manage_guild=True)
    async def set_warning_action(self, ctx, warnings: int, action: str, duration: str = None):
        """Set an action for reaching a warning count"""
        if warnings < 1 or warnings > 50:
            embed = EmbedTemplates.error(
                "Invalid Warning Count",
                "Warning count must be between 1 and 50!",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        action = action.lower()
        if action not in ['mute', 'kick', 'ban']:
            embed = EmbedTemplates.error(
                "Invalid Action",
                "Action must be: mute, kick, or ban",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
        
        # Validate duration for mute
        if action == 'mute' and duration:
            mod_cog = self.bot.get_cog('Moderation')
            if mod_cog and not mod_cog.parse_time(duration):
                embed = EmbedTemplates.error(
                    "Invalid Duration",
                    "Duration format should be like `5m`, `2h`, `1d` (m=minutes, h=hours, d=days)",
                    ctx.author
                )
                await ctx.send(embed=embed)
                return
        
        try:
            async with self.bot.db.acquire() as conn:
                await conn.execute("""
                    INSERT INTO warning_actions (guild_id, warning_count, action_type, duration)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (guild_id, warning_count) DO UPDATE SET
                        action_type = $3, duration = $4
                """, ctx.guild.id, warnings, action, duration or 'permanent')
                
                duration_text = f" for {duration}" if duration and action == 'mute' else ""
                embed = EmbedTemplates.success(
                    "Warning Action Set",
                    f"Users will be **{action}d**{duration_text} when they reach **{warnings}** warning{'s' if warnings != 1 else ''}!",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to set action.", ctx.author)
            await ctx.send(embed=embed)
    
    @automod.command(name='remove-action')
    @commands.has_permissions(manage_guild=True)
    async def remove_warning_action(self, ctx, warnings: int):
        """Remove a warning action"""
        try:
            async with self.bot.db.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM warning_actions 
                    WHERE guild_id = $1 AND warning_count = $2
                """, ctx.guild.id, warnings)
                
                if result == "DELETE 0":
                    embed = EmbedTemplates.error(
                        "Action Not Found",
                        f"No action found for {warnings} warning{'s' if warnings != 1 else ''}.",
                        ctx.author
                    )
                else:
                    embed = EmbedTemplates.success(
                        "Warning Action Removed",
                        f"Removed action for {warnings} warning{'s' if warnings != 1 else ''}!",
                        ctx.author
                    )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to remove action.", ctx.author)
            await ctx.send(embed=embed)
    
    @automod.command(name='links')
    @commands.has_permissions(manage_guild=True)
    async def toggle_links(self, ctx):
        """Toggle Discord link blocking"""
        try:
            async with self.bot.db.acquire() as conn:
                current = await conn.fetchval(
                    "SELECT discord_links_enabled FROM automod_settings WHERE guild_id = $1", ctx.guild.id
                )
                new_state = not current if current is not None else True
                
                await conn.execute(
                    """INSERT INTO automod_settings (guild_id, discord_links_enabled) VALUES ($1, $2)
                       ON CONFLICT (guild_id) DO UPDATE SET discord_links_enabled = $2""",
                    ctx.guild.id, new_state
                )
                
                status = "enabled" if new_state else "disabled"
                embed = EmbedTemplates.success(
                    "Discord Link Blocking Updated", 
                    f"Discord link blocking has been **{status}**!",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
            await ctx.send(embed=embed)
    
    @automod.command(name='spam')
    @commands.has_permissions(manage_guild=True) 
    async def toggle_spam(self, ctx):
        """Toggle spam detection"""
        try:
            async with self.bot.db.acquire() as conn:
                current = await conn.fetchval(
                    "SELECT spam_enabled FROM automod_settings WHERE guild_id = $1", ctx.guild.id
                )
                new_state = not current if current is not None else True
                
                await conn.execute(
                    """INSERT INTO automod_settings (guild_id, spam_enabled) VALUES ($1, $2)
                       ON CONFLICT (guild_id) DO UPDATE SET spam_enabled = $2""",
                    ctx.guild.id, new_state
                )
                
                status = "enabled" if new_state else "disabled"
                embed = EmbedTemplates.success(
                    "Spam Detection Updated",
                    f"Spam detection has been **{status}**!",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
            await ctx.send(embed=embed)
    
    @automod.command(name='nsfw')
    @commands.has_permissions(manage_guild=True)
    async def toggle_nsfw(self, ctx):
        """Toggle NSFW content filtering"""
        try:
            async with self.bot.db.acquire() as conn:
                current = await conn.fetchval(
                    "SELECT nsfw_enabled FROM automod_settings WHERE guild_id = $1", ctx.guild.id
                )
                new_state = not current if current is not None else True
                
                await conn.execute(
                    """INSERT INTO automod_settings (guild_id, nsfw_enabled) VALUES ($1, $2)
                       ON CONFLICT (guild_id) DO UPDATE SET nsfw_enabled = $2""",
                    ctx.guild.id, new_state
                )
                
                status = "enabled" if new_state else "disabled"
                embed = EmbedTemplates.success(
                    "NSFW Filter Updated", 
                    f"NSFW content filtering has been **{status}**!",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
            await ctx.send(embed=embed)
    
    @automod.command(name='spam-config')
    @commands.has_permissions(manage_guild=True)
    async def configure_spam(self, ctx, messages: int = None, seconds: int = None):
        """Configure spam detection settings"""
        if messages is None or seconds is None:
            embed = EmbedTemplates.error(
                "Missing Arguments",
                "Please provide both messages and seconds!\nExample: `.automod spam-config 5 10`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if messages < 2 or messages > 20:
            embed = EmbedTemplates.error(
                "Invalid Messages",
                "Messages must be between 2 and 20!",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if seconds < 5 or seconds > 60:
            embed = EmbedTemplates.error(
                "Invalid Time",
                "Seconds must be between 5 and 60!",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
        
        try:
            async with self.bot.db.acquire() as conn:
                await conn.execute(
                    """INSERT INTO automod_settings (guild_id, spam_messages, spam_time) VALUES ($1, $2, $3)
                       ON CONFLICT (guild_id) DO UPDATE SET spam_messages = $2, spam_time = $3""",
                    ctx.guild.id, messages, seconds
                )
                
                embed = EmbedTemplates.success(
                    "Spam Settings Updated",
                    f"Spam detection will now trigger after **{messages}** messages in **{seconds}** seconds!",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))