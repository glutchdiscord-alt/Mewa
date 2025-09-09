import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
import asyncpg
from aiohttp import web
import aiohttp

load_dotenv()

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=self.get_prefix_sync,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.db = None
        self.prefixes = {}  # guild_id: prefix
        self.web_server = None
        
    def get_prefix_sync(self, message):
        return '.'
        
    async def get_prefix(self, message):
        if not message.guild:
            return '.'
        
        guild_id = message.guild.id
        if guild_id in self.prefixes:
            return self.prefixes[guild_id]
        
        # Get from database
        if self.db:
            try:
                result = await self.db.fetchval(
                    "SELECT prefix FROM guild_settings WHERE guild_id = $1", 
                    guild_id
                )
                if result:
                    self.prefixes[guild_id] = result
                    return result
            except:
                pass
                
        # Default prefix
        self.prefixes[guild_id] = '.'
        return '.'
        
    async def setup_hook(self):
        # Connect to database
        try:
            self.db = await asyncpg.create_pool(os.getenv('DATABASE_URL'))
            await self.create_tables()
            print("Database connected successfully!")
        except Exception as e:
            print(f"Database connection failed: {e}")
            
        # Load cogs
        await self.load_extension('cogs.help')
        await self.load_extension('cogs.moderation')  
        await self.load_extension('cogs.leveling')
        await self.load_extension('cogs.automod')
        await self.load_extension('cogs.welcome')
        await self.load_extension('cogs.games')
        
        # Start web server for health checks
        await self.start_web_server()
        
        # Start keep-alive task
        asyncio.create_task(self.keep_alive_task())
        
        print("Bot setup completed!")
        
    async def create_tables(self):
        if not self.db:
            return
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id BIGINT PRIMARY KEY,
                prefix TEXT DEFAULT '.'
            )
        """)
        
        if self.db:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS user_levels (
                user_id BIGINT,
                guild_id BIGINT,
                xp BIGINT DEFAULT 0,
                level INT DEFAULT 0,
                messages INT DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        
        if self.db:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                guild_id BIGINT,
                moderator_id BIGINT,
                reason TEXT,
                warned_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        if self.db:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS automod_settings (
                guild_id BIGINT PRIMARY KEY,
                warnings_enabled BOOLEAN DEFAULT FALSE,
                discord_links_enabled BOOLEAN DEFAULT FALSE,
                spam_enabled BOOLEAN DEFAULT FALSE,
                spam_messages INTEGER DEFAULT 5,
                spam_time INTEGER DEFAULT 10,
                nsfw_enabled BOOLEAN DEFAULT FALSE
            )
        """)
        
        if self.db:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS welcome_settings (
                guild_id BIGINT PRIMARY KEY,
                welcome_enabled BOOLEAN DEFAULT FALSE,
                leave_enabled BOOLEAN DEFAULT FALSE,
                welcome_channel BIGINT,
                leave_channel BIGINT,
                welcome_message TEXT DEFAULT 'Welcome {user} to {server}! 🎉',
                leave_message TEXT DEFAULT '{user} has left {server}. 👋'
            )
        """)
        
        if self.db:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS leveling_settings (
                guild_id BIGINT PRIMARY KEY,
                leveling_enabled BOOLEAN DEFAULT TRUE
            )
        """)
        
        if self.db:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS muted_users (
                user_id BIGINT,
                guild_id BIGINT,
                role_id BIGINT,
                muted_at TIMESTAMP DEFAULT NOW(),
                unmute_at TIMESTAMP,
                reason TEXT,
                moderator_id BIGINT,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        
        if self.db:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS warning_actions (
                guild_id BIGINT,
                warning_count INTEGER,
                action_type TEXT,
                duration TEXT,
                PRIMARY KEY (guild_id, warning_count)
            )
        """)
        
    async def health_check(self, request):
        """Health endpoint for external monitoring"""
        return web.Response(text="Bot is alive!")
    
    async def start_web_server(self):
        """Start web server for health checks"""
        try:
            app = web.Application()
            app.router.add_get('/health', self.health_check)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', 5000)
            await site.start()
            print("Health server running on port 5000")
            self.web_server = runner
        except Exception as e:
            print(f"Failed to start web server: {e}")
    
    async def keep_alive_task(self):
        """Self-ping to prevent sleep"""
        await asyncio.sleep(30)  # Wait for bot to fully start
        
        while not self.is_closed():
            try:
                # Get the external URL from environment (Render sets RENDER_EXTERNAL_URL)
                url = os.getenv('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
                
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(f"{url}/health") as response:
                        if response.status == 200:
                            print("✅ Keep-alive ping successful")
                        else:
                            print(f"⚠️ Keep-alive ping failed: {response.status}")
            except Exception as e:
                print(f"❌ Keep-alive ping error: {e}")
            
            # Wait 14 minutes (840 seconds) before next ping
            await asyncio.sleep(840)
    
    async def on_ready(self):
        print(f'{self.user} has landed! 🚀')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="my default prefix is ."
        )
        await self.change_presence(activity=activity)
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

if __name__ == "__main__":
    bot = DiscordBot()
    
    @bot.tree.command(name="prefix", description="Change the bot's prefix for this server")
    @discord.app_commands.describe(new_prefix="The new prefix to use")
    async def change_prefix(interaction: discord.Interaction, new_prefix: str):
        if not interaction.user.guild_permissions or not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need `Manage Server` permission to change the prefix.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if len(new_prefix) > 5:
            embed = discord.Embed(
                title="❌ Invalid Prefix",
                description="Prefix must be 5 characters or less.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if not interaction.guild:
            return
            
        guild_id = interaction.guild.id
        
        try:
            if bot.db:
                await bot.db.execute("""
                INSERT INTO guild_settings (guild_id, prefix) 
                VALUES ($1, $2) 
                ON CONFLICT (guild_id) 
                DO UPDATE SET prefix = $2
            """, guild_id, new_prefix)
            
            bot.prefixes[guild_id] = new_prefix
            
            embed = discord.Embed(
                title="✅ Prefix Updated",
                description=f"Server prefix has been changed to `{new_prefix}`",
                color=0x4ecdc4
            )
            embed.set_footer(text=f"Changed by {interaction.user.display_name}")
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to update prefix. Please try again.",
                color=0xff6b6b
            )
            
        await interaction.response.send_message(embed=embed)
    
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("DISCORD_TOKEN not found in environment variables!")