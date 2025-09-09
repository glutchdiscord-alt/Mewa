import discord
from discord.ext import commands
from utils.embeds import EmbedTemplates

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def get_welcome_settings(self, guild_id):
        """Get welcome/leave settings for a guild"""
        try:
            async with self.bot.db.acquire() as conn:
                settings = await conn.fetchrow(
                    "SELECT * FROM welcome_settings WHERE guild_id = $1", guild_id
                )
                if not settings:
                    return {
                        'welcome_enabled': False,
                        'leave_enabled': False,
                        'welcome_channel': None,
                        'leave_channel': None,
                        'welcome_message': "Welcome {user} to {server}! 🎉",
                        'leave_message': "{user} has left {server}. 👋"
                    }
                return dict(settings)
        except Exception as e:
            print(f"Error getting welcome settings: {e}")
            return {
                'welcome_enabled': False,
                'leave_enabled': False,
                'welcome_channel': None,
                'leave_channel': None,
                'welcome_message': "Welcome {user} to {server}! 🎉",
                'leave_message': "{user} has left {server}. 👋"
            }
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        settings = await self.get_welcome_settings(member.guild.id)
        
        if not settings['welcome_enabled'] or not settings['welcome_channel']:
            return
            
        channel = self.bot.get_channel(settings['welcome_channel'])
        if not channel:
            return
            
        try:
            message = settings['welcome_message'].format(
                user=member.mention,
                server=member.guild.name,
                name=member.display_name
            )
            
            embed = discord.Embed(
                title="🎉 Welcome!",
                description=message,
                color=0x4ecdc4
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text=f"Member #{member.guild.member_count}")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error sending welcome message: {e}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        settings = await self.get_welcome_settings(member.guild.id)
        
        if not settings['leave_enabled'] or not settings['leave_channel']:
            return
            
        channel = self.bot.get_channel(settings['leave_channel'])
        if not channel:
            return
            
        try:
            message = settings['leave_message'].format(
                user=member.display_name,
                server=member.guild.name,
                name=member.display_name
            )
            
            embed = discord.Embed(
                title="👋 Goodbye",
                description=message,
                color=0xff6b6b
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text=f"Members remaining: {member.guild.member_count}")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error sending leave message: {e}")
    
    @commands.group(name='welcome', invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def welcome(self, ctx):
        """Welcome/leave message settings"""
        settings = await self.get_welcome_settings(ctx.guild.id)
        
        embed = discord.Embed(
            title="👋 Welcome/Leave Settings",
            color=0x5865f2
        )
        
        # Welcome settings
        welcome_status = "✅ Enabled" if settings['welcome_enabled'] else "❌ Disabled"
        welcome_channel = f"<#{settings['welcome_channel']}>" if settings['welcome_channel'] else "Not set"
        
        embed.add_field(
            name="🎉 Welcome Messages",
            value=f"**Status:** {welcome_status}\n**Channel:** {welcome_channel}",
            inline=True
        )
        
        # Leave settings  
        leave_status = "✅ Enabled" if settings['leave_enabled'] else "❌ Disabled"
        leave_channel = f"<#{settings['leave_channel']}>" if settings['leave_channel'] else "Not set"
        
        embed.add_field(
            name="👋 Leave Messages", 
            value=f"**Status:** {leave_status}\n**Channel:** {leave_channel}",
            inline=True
        )
        
        embed.add_field(name="\u200b", value="\u200b", inline=True)  # Empty field for spacing
        
        # Messages
        embed.add_field(
            name="💬 Welcome Message",
            value=f"```{settings['welcome_message']}```",
            inline=False
        )
        
        embed.add_field(
            name="💬 Leave Message", 
            value=f"```{settings['leave_message']}```",
            inline=False
        )
        
        prefix = await self.bot.get_prefix(ctx.message)
        if isinstance(prefix, list):
            prefix = prefix[0]
            
        embed.add_field(
            name="🔧 Commands",
            value=f"`{prefix}welcome toggle` - Toggle welcome messages\n"
                  f"`{prefix}welcome leave` - Toggle leave messages\n"
                  f"`{prefix}welcome channel <#channel>` - Set welcome channel\n"
                  f"`{prefix}welcome leave-channel <#channel>` - Set leave channel\n"
                  f"`{prefix}welcome message <message>` - Set welcome message\n"
                  f"`{prefix}welcome leave-message <message>` - Set leave message",
            inline=False
        )
        
        embed.set_footer(text="Use {user}, {server}, {name} in messages")
        await ctx.send(embed=embed)
    
    @welcome.command(name='toggle')
    @commands.has_permissions(manage_guild=True)
    async def toggle_welcome(self, ctx):
        """Toggle welcome messages"""
        try:
            async with self.bot.db.acquire() as conn:
                current = await conn.fetchval(
                    "SELECT welcome_enabled FROM welcome_settings WHERE guild_id = $1", ctx.guild.id
                )
                new_state = not current if current is not None else True
                
                await conn.execute(
                    """INSERT INTO welcome_settings (guild_id, welcome_enabled) VALUES ($1, $2)
                       ON CONFLICT (guild_id) DO UPDATE SET welcome_enabled = $2""",
                    ctx.guild.id, new_state
                )
                
                status = "enabled" if new_state else "disabled"
                embed = EmbedTemplates.success(
                    "Welcome Messages Updated",
                    f"Welcome messages have been **{status}**!",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
            await ctx.send(embed=embed)
    
    @welcome.command(name='leave')
    @commands.has_permissions(manage_guild=True)
    async def toggle_leave(self, ctx):
        """Toggle leave messages"""
        try:
            async with self.bot.db.acquire() as conn:
                current = await conn.fetchval(
                    "SELECT leave_enabled FROM welcome_settings WHERE guild_id = $1", ctx.guild.id
                )
                new_state = not current if current is not None else True
                
                await conn.execute(
                    """INSERT INTO welcome_settings (guild_id, leave_enabled) VALUES ($1, $2)
                       ON CONFLICT (guild_id) DO UPDATE SET leave_enabled = $2""",
                    ctx.guild.id, new_state
                )
                
                status = "enabled" if new_state else "disabled"
                embed = EmbedTemplates.success(
                    "Leave Messages Updated",
                    f"Leave messages have been **{status}**!",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
            await ctx.send(embed=embed)
    
    @welcome.command(name='channel')
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_channel(self, ctx, channel: discord.TextChannel = None):
        """Set welcome channel"""
        if not channel:
            embed = EmbedTemplates.error(
                "Missing Channel",
                "Please mention a channel!\nExample: `.welcome channel #general`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        try:
            async with self.bot.db.acquire() as conn:
                await conn.execute(
                    """INSERT INTO welcome_settings (guild_id, welcome_channel) VALUES ($1, $2)
                       ON CONFLICT (guild_id) DO UPDATE SET welcome_channel = $2""",
                    ctx.guild.id, channel.id
                )
                
                embed = EmbedTemplates.success(
                    "Welcome Channel Set",
                    f"Welcome messages will be sent to {channel.mention}!",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
            await ctx.send(embed=embed)
    
    @welcome.command(name='leave-channel')
    @commands.has_permissions(manage_guild=True)
    async def set_leave_channel(self, ctx, channel: discord.TextChannel = None):
        """Set leave channel"""
        if not channel:
            embed = EmbedTemplates.error(
                "Missing Channel",
                "Please mention a channel!\nExample: `.welcome leave-channel #general`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        try:
            async with self.bot.db.acquire() as conn:
                await conn.execute(
                    """INSERT INTO welcome_settings (guild_id, leave_channel) VALUES ($1, $2)
                       ON CONFLICT (guild_id) DO UPDATE SET leave_channel = $2""",
                    ctx.guild.id, channel.id
                )
                
                embed = EmbedTemplates.success(
                    "Leave Channel Set",
                    f"Leave messages will be sent to {channel.mention}!",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
            await ctx.send(embed=embed)
    
    @welcome.command(name='message')
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_message(self, ctx, *, message: str = None):
        """Set welcome message"""
        if not message:
            embed = EmbedTemplates.error(
                "Missing Message",
                "Please provide a welcome message!\nExample: `.welcome message Welcome {user} to our server! 🎉`\n\nVariables: `{user}`, `{server}`, `{name}`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if len(message) > 500:
            embed = EmbedTemplates.error(
                "Message Too Long",
                "Welcome message must be 500 characters or less!",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        try:
            async with self.bot.db.acquire() as conn:
                await conn.execute(
                    """INSERT INTO welcome_settings (guild_id, welcome_message) VALUES ($1, $2)
                       ON CONFLICT (guild_id) DO UPDATE SET welcome_message = $2""",
                    ctx.guild.id, message
                )
                
                embed = EmbedTemplates.success(
                    "Welcome Message Set",
                    f"Welcome message updated!\n\n**Preview:**\n{message.format(user='@User', server=ctx.guild.name, name='User')}",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
            await ctx.send(embed=embed)
    
    @welcome.command(name='leave-message')
    @commands.has_permissions(manage_guild=True)
    async def set_leave_message(self, ctx, *, message: str = None):
        """Set leave message"""
        if not message:
            embed = EmbedTemplates.error(
                "Missing Message",
                "Please provide a leave message!\nExample: `.welcome leave-message {user} has left us. 👋`\n\nVariables: `{user}`, `{server}`, `{name}`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if len(message) > 500:
            embed = EmbedTemplates.error(
                "Message Too Long",
                "Leave message must be 500 characters or less!",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        try:
            async with self.bot.db.acquire() as conn:
                await conn.execute(
                    """INSERT INTO welcome_settings (guild_id, leave_message) VALUES ($1, $2)
                       ON CONFLICT (guild_id) DO UPDATE SET leave_message = $2""",
                    ctx.guild.id, message
                )
                
                embed = EmbedTemplates.success(
                    "Leave Message Set",
                    f"Leave message updated!\n\n**Preview:**\n{message.format(user='User', server=ctx.guild.name, name='User')}",
                    ctx.author
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = EmbedTemplates.error("Database Error", "Failed to update settings.", ctx.author)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))