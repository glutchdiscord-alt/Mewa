import discord
from discord.ext import commands
import random
import asyncio
from utils.embeds import EmbedTemplates

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trivia_questions = [
            {"question": "What is the capital of France?", "answer": "Paris", "options": ["London", "Berlin", "Paris", "Madrid"]},
            {"question": "Which planet is known as the Red Planet?", "answer": "Mars", "options": ["Venus", "Mars", "Jupiter", "Saturn"]},
            {"question": "What is 2 + 2?", "answer": "4", "options": ["3", "4", "5", "6"]},
            {"question": "Who painted the Mona Lisa?", "answer": "Leonardo da Vinci", "options": ["Pablo Picasso", "Vincent van Gogh", "Leonardo da Vinci", "Michelangelo"]},
            {"question": "What is the largest mammal in the world?", "answer": "Blue Whale", "options": ["Elephant", "Blue Whale", "Giraffe", "Hippopotamus"]},
            {"question": "Which programming language is known for web development?", "answer": "JavaScript", "options": ["Python", "C++", "JavaScript", "Assembly"]},
            {"question": "What year did World War II end?", "answer": "1945", "options": ["1944", "1945", "1946", "1947"]},
            {"question": "What is the chemical symbol for gold?", "answer": "Au", "options": ["Go", "Gd", "Au", "Ag"]},
        ]
        
        self.eightball_responses = [
            "🎱 It is certain",
            "🎱 Without a doubt", 
            "🎱 Yes definitely",
            "🎱 You may rely on it",
            "🎱 As I see it, yes",
            "🎱 Most likely",
            "🎱 Outlook good",
            "🎱 Yes",
            "🎱 Signs point to yes",
            "🎱 Reply hazy, try again",
            "🎱 Ask again later",
            "🎱 Better not tell you now",
            "🎱 Cannot predict now",
            "🎱 Concentrate and ask again",
            "🎱 Don't count on it",
            "🎱 My reply is no",
            "🎱 My sources say no",
            "🎱 Outlook not so good",
            "🎱 Very doubtful"
        ]
        
        self.would_you_rather = [
            "Would you rather have the ability to fly or be invisible?",
            "Would you rather live underwater or in space?",
            "Would you rather have super strength or super speed?",
            "Would you rather be able to read minds or see the future?",
            "Would you rather always be 10 minutes late or 20 minutes early?",
            "Would you rather have unlimited money or unlimited free time?",
            "Would you rather never use social media again or never watch another movie?",
            "Would you rather be famous or be the best friend of someone famous?",
        ]
        
        self.flags = [
            {"flag": "🇺🇸", "country": "United States", "options": ["Canada", "United States", "Mexico", "Brazil"]},
            {"flag": "🇫🇷", "country": "France", "options": ["Spain", "Italy", "France", "Germany"]},
            {"flag": "🇯🇵", "country": "Japan", "options": ["China", "South Korea", "Japan", "Thailand"]},
            {"flag": "🇩🇪", "country": "Germany", "options": ["Austria", "Germany", "Netherlands", "Belgium"]},
            {"flag": "🇧🇷", "country": "Brazil", "options": ["Argentina", "Brazil", "Chile", "Peru"]},
            {"flag": "🇨🇦", "country": "Canada", "options": ["Canada", "United States", "Greenland", "Iceland"]},
            {"flag": "🇮🇹", "country": "Italy", "options": ["Spain", "Italy", "Greece", "France"]},
            {"flag": "🇪🇸", "country": "Spain", "options": ["Portugal", "Spain", "France", "Italy"]},
            {"flag": "🇦🇺", "country": "Australia", "options": ["New Zealand", "Australia", "Fiji", "Papua New Guinea"]},
            {"flag": "🇬🇧", "country": "United Kingdom", "options": ["Ireland", "United Kingdom", "Scotland", "Wales"]},
            {"flag": "🇰🇷", "country": "South Korea", "options": ["North Korea", "South Korea", "Japan", "China"]},
            {"flag": "🇮🇳", "country": "India", "options": ["Pakistan", "India", "Bangladesh", "Sri Lanka"]},
            {"flag": "🇳🇱", "country": "Netherlands", "options": ["Belgium", "Netherlands", "Luxembourg", "Denmark"]},
            {"flag": "🇸🇪", "country": "Sweden", "options": ["Norway", "Sweden", "Finland", "Denmark"]},
            {"flag": "🇷🇺", "country": "Russia", "options": ["Poland", "Russia", "Ukraine", "Belarus"]},
        ]
        
        self.slot_symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣"]
        self.slot_payouts = {
            "💎💎💎": 100,
            "7️⃣7️⃣7️⃣": 50,
            "⭐⭐⭐": 25,
            "🍇🍇🍇": 15,
            "🍊🍊🍊": 10,
            "🍋🍋🍋": 8,
            "🍒🍒🍒": 5,
        }
        
        self.tictactoe_games = {}  # user_id: game_data
        self.active_games = {}  # channel_id: game_data (for flag/trivia games)
        
    @commands.command(name='rps', aliases=['rockpaperscissors'])
    async def rock_paper_scissors(self, ctx, choice: str = None):
        if not choice or choice.lower() not in ['rock', 'paper', 'scissors', 'r', 'p', 's']:
            embed = EmbedTemplates.error(
                "Invalid Choice",
                "Please choose: `rock`, `paper`, or `scissors`\nExample: `.rps rock`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        # Normalize user input
        user_choice = choice.lower()
        if user_choice in ['r', 'rock']:
            user_choice = 'rock'
        elif user_choice in ['p', 'paper']:
            user_choice = 'paper'
        elif user_choice in ['s', 'scissors']:
            user_choice = 'scissors'
            
        bot_choice = random.choice(['rock', 'paper', 'scissors'])
        
        # Determine winner
        if user_choice == bot_choice:
            result = "It's a tie!"
            color = 0xffa726
            emoji = "🤝"
        elif (user_choice == 'rock' and bot_choice == 'scissors') or \
             (user_choice == 'paper' and bot_choice == 'rock') or \
             (user_choice == 'scissors' and bot_choice == 'paper'):
            result = "You win!"
            color = 0x4ecdc4
            emoji = "🎉"
        else:
            result = "I win!"
            color = 0xff6b6b
            emoji = "🤖"
            
        # Create embed
        embed = discord.Embed(
            title=f"{emoji} Rock Paper Scissors",
            description=f"**{result}**",
            color=color
        )
        
        choice_emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
        embed.add_field(name="Your Choice", value=f"{choice_emojis[user_choice]} {user_choice.title()}", inline=True)
        embed.add_field(name="My Choice", value=f"{choice_emojis[bot_choice]} {bot_choice.title()}", inline=True)
        
        embed.set_footer(text=f"Played by {ctx.author.display_name}")
        await ctx.send(embed=embed)
        
    @commands.command(name='guess', aliases=['number'])
    async def number_guess(self, ctx, guess: int = None):
        if guess is None:
            embed = EmbedTemplates.error(
                "Missing Number",
                "Please guess a number between 1 and 100!\nExample: `.guess 42`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if guess < 1 or guess > 100:
            embed = EmbedTemplates.error(
                "Invalid Range",
                "Please guess a number between 1 and 100!",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        secret_number = random.randint(1, 100)
        
        if guess == secret_number:
            embed = discord.Embed(
                title="🎯 Perfect Shot!",
                description=f"**Wow! You guessed it exactly!**\nThe number was **{secret_number}**",
                color=0xffd700
            )
        elif abs(guess - secret_number) <= 5:
            embed = discord.Embed(
                title="🔥 So Close!",
                description=f"You were super close! You guessed **{guess}**, but it was **{secret_number}**",
                color=0x4ecdc4
            )
        elif abs(guess - secret_number) <= 15:
            embed = discord.Embed(
                title="👍 Not Bad!",
                description=f"Pretty good guess! You guessed **{guess}**, but it was **{secret_number}**",
                color=0x9b59b6
            )
        else:
            embed = discord.Embed(
                title="💭 Keep Trying!",
                description=f"You guessed **{guess}**, but it was **{secret_number}**. Better luck next time!",
                color=0xff6b6b
            )
            
        embed.set_footer(text=f"Played by {ctx.author.display_name}")
        await ctx.send(embed=embed)
        
    @commands.command(name='8ball', aliases=['eightball', 'ask'])
    async def magic_8ball(self, ctx, *, question: str = None):
        if not question:
            embed = EmbedTemplates.error(
                "Missing Question",
                "Please ask the magic 8-ball a question!\nExample: `.8ball Will I win the lottery?`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if len(question) > 200:
            embed = EmbedTemplates.error(
                "Question Too Long",
                "Please keep your question under 200 characters!",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        response = random.choice(self.eightball_responses)
        
        embed = discord.Embed(
            title="🔮 Magic 8-Ball",
            color=0x5865f2
        )
        
        embed.add_field(name="❓ Question", value=question, inline=False)
        embed.add_field(name="✨ Answer", value=response, inline=False)
        
        embed.set_footer(text=f"Asked by {ctx.author.display_name}")
        await ctx.send(embed=embed)
        
    @commands.command(name='coinflip', aliases=['flip', 'coin'])
    async def coin_flip(self, ctx):
        result = random.choice(['Heads', 'Tails'])
        emoji = '🪙' if result == 'Heads' else '🔘'
        
        embed = discord.Embed(
            title=f"{emoji} Coin Flip",
            description=f"**The coin landed on {result}!**",
            color=0xffd700
        )
        
        embed.set_footer(text=f"Flipped by {ctx.author.display_name}")
        await ctx.send(embed=embed)
        
    @commands.command(name='dice', aliases=['roll'])
    async def dice_roll(self, ctx, sides: int = 6):
        if sides < 2 or sides > 100:
            embed = EmbedTemplates.error(
                "Invalid Dice",
                "Please choose a dice with 2-100 sides!\nExample: `.dice 20` for a 20-sided die",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        result = random.randint(1, sides)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"**You rolled a {result}!**",
            color=0xe74c3c
        )
        
        embed.add_field(name="Die Type", value=f"D{sides}", inline=True)
        embed.add_field(name="Result", value=f"**{result}**", inline=True)
        
        embed.set_footer(text=f"Rolled by {ctx.author.display_name}")
        await ctx.send(embed=embed)
        
    @commands.command(name='trivia')
    async def trivia(self, ctx):
        if ctx.channel.id in self.active_games:
            embed = EmbedTemplates.error("Game Active", "A game is already running in this channel!", ctx.author)
            await ctx.send(embed=embed)
            return
            
        question_data = random.choice(self.trivia_questions)
        
        # Store active game
        self.active_games[ctx.channel.id] = {
            'type': 'trivia',
            'answer': question_data['answer'].lower(),
            'started_by': ctx.author
        }
        
        embed = discord.Embed(
            title="🧠 Trivia",
            description=f"{question_data['question']}\n\nType your answer to win!",
            color=0x9b59b6
        )
        
        await ctx.send(embed=embed)
        
        # Wait for correct answer
        def check(message):
            return (message.channel.id == ctx.channel.id and 
                   not message.author.bot and
                   message.content.lower().strip() == question_data['answer'].lower())
        
        try:
            winner_message = await self.bot.wait_for('message', timeout=30.0, check=check)
            
            # Winner found
            embed = discord.Embed(
                title="🎉 Winner!",
                description=f"{winner_message.author.mention} got it! The answer was **{question_data['answer']}**\n\nType `.trivia` to start a new game!",
                color=0x4ecdc4
            )
            await ctx.send(embed=embed)
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Time's Up!",
                description=f"The answer was **{question_data['answer']}**\n\nType `.trivia` to start a new game!",
                color=0xffa726
            )
            await ctx.send(embed=embed)
        finally:
            # Remove active game
            if ctx.channel.id in self.active_games:
                del self.active_games[ctx.channel.id]
            
    @commands.command(name='wyr', aliases=['wouldyourather'])
    async def would_you_rather(self, ctx):
        question = random.choice(self.would_you_rather)
        
        embed = discord.Embed(
            title="🤔 Would You Rather",
            description=question,
            color=0x8e44ad
        )
        
        embed.set_footer(text=f"Think about it, {ctx.author.display_name}!")
        await ctx.send(embed=embed)
        
    @commands.command(name='flag', aliases=['guesstheflag', 'flagguess'])
    async def guess_the_flag(self, ctx):
        if ctx.channel.id in self.active_games:
            embed = EmbedTemplates.error("Game Active", "A game is already running in this channel!", ctx.author)
            await ctx.send(embed=embed)
            return
            
        flag_data = random.choice(self.flags)
        
        # Store active game
        self.active_games[ctx.channel.id] = {
            'type': 'flag',
            'answer': flag_data['country'].lower(),
            'started_by': ctx.author
        }
        
        embed = discord.Embed(
            title="🏁 Guess the Flag",
            description=f"{flag_data['flag']}\n\nType the country name to win!",
            color=0x3498db
        )
        
        await ctx.send(embed=embed)
        
        # Wait for correct answer
        def check(message):
            return (message.channel.id == ctx.channel.id and 
                   not message.author.bot and
                   message.content.lower().strip() == flag_data['country'].lower())
        
        try:
            winner_message = await self.bot.wait_for('message', timeout=30.0, check=check)
            
            # Winner found
            embed = discord.Embed(
                title="🎉 Winner!",
                description=f"{winner_message.author.mention} got it! The answer was **{flag_data['country']}**\n\nType `.flag` to start a new game!",
                color=0x4ecdc4
            )
            await ctx.send(embed=embed)
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Time's Up!",
                description=f"The answer was **{flag_data['country']}**\n\nType `.flag` to start a new game!",
                color=0xffa726
            )
            await ctx.send(embed=embed)
        finally:
            # Remove active game
            if ctx.channel.id in self.active_games:
                del self.active_games[ctx.channel.id]
            
    @commands.command(name='blackjack', aliases=['bj', '21'])
    async def blackjack(self, ctx):
        # Create deck
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = [(rank, suit) for suit in suits for rank in ranks]
        random.shuffle(deck)
        
        # Deal cards
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        def card_value(hand):
            value = 0
            aces = 0
            for rank, _ in hand:
                if rank in ['J', 'Q', 'K']:
                    value += 10
                elif rank == 'A':
                    aces += 1
                    value += 11
                else:
                    value += int(rank)
            
            # Handle aces
            while value > 21 and aces:
                value -= 10
                aces -= 1
            return value
        
        def format_hand(hand, hide_first=False):
            if hide_first:
                return f"🎴 {hand[1][0]}{hand[1][1]}"
            return " ".join([f"{card[0]}{card[1]}" for card in hand])
        
        player_value = card_value(player_hand)
        dealer_value = card_value(dealer_hand)
        
        # Initial embed
        embed = discord.Embed(title="🃏 Blackjack", color=0x2c3e50)
        embed.add_field(name=f"Your Hand ({player_value})", value=format_hand(player_hand), inline=True)
        embed.add_field(name="Dealer's Hand", value=format_hand(dealer_hand, True), inline=True)
        
        if player_value == 21:
            embed.add_field(name="Result", value="🎉 Blackjack! You win!", inline=False)
            embed.color = 0x4ecdc4
            await ctx.send(embed=embed)
            return
        
        embed.add_field(name="Actions", value="React with ✋ to Hit or 🛑 to Stand", inline=False)
        message = await ctx.send(embed=embed)
        
        await message.add_reaction('✋')
        await message.add_reaction('🛑')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✋', '🛑'] and reaction.message.id == message.id
        
        # Player's turn
        while player_value < 21:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == '✋':  # Hit
                    player_hand.append(deck.pop())
                    player_value = card_value(player_hand)
                    
                    embed = discord.Embed(title="🃏 Blackjack", color=0x2c3e50)
                    embed.add_field(name=f"Your Hand ({player_value})", value=format_hand(player_hand), inline=True)
                    embed.add_field(name="Dealer's Hand", value=format_hand(dealer_hand, True), inline=True)
                    
                    if player_value > 21:
                        embed.add_field(name="Result", value="💥 Bust! You lose!", inline=False)
                        embed.color = 0xff6b6b
                        await ctx.send(embed=embed)
                        return
                    elif player_value == 21:
                        break
                    else:
                        embed.add_field(name="Actions", value="React with ✋ to Hit or 🛑 to Stand", inline=False)
                        
                    await ctx.send(embed=embed)
                    
                elif str(reaction.emoji) == '🛑':  # Stand
                    break
                    
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⏰ Time's Up!",
                    description="You took too long! Game over.",
                    color=0xffa726
                )
                await ctx.send(embed=embed)
                return
        
        # Dealer's turn
        while dealer_value < 17:
            dealer_hand.append(deck.pop())
            dealer_value = card_value(dealer_hand)
        
        # Final result
        embed = discord.Embed(title="🃏 Blackjack - Final Result", color=0x2c3e50)
        embed.add_field(name=f"Your Hand ({player_value})", value=format_hand(player_hand), inline=True)
        embed.add_field(name=f"Dealer's Hand ({dealer_value})", value=format_hand(dealer_hand), inline=True)
        
        if dealer_value > 21:
            embed.add_field(name="Result", value="🎉 Dealer busts! You win!", inline=False)
            embed.color = 0x4ecdc4
        elif player_value > dealer_value:
            embed.add_field(name="Result", value="🎉 You win!", inline=False)
            embed.color = 0x4ecdc4
        elif player_value == dealer_value:
            embed.add_field(name="Result", value="🤝 Push (Tie)!", inline=False)
            embed.color = 0xffa726
        else:
            embed.add_field(name="Result", value="😔 Dealer wins!", inline=False)
            embed.color = 0xff6b6b
        
        await ctx.send(embed=embed)
        
    @commands.command(name='slots', aliases=['slot', 'slotmachine'])
    async def slots(self, ctx):
        # Spin the slots
        result = [random.choice(self.slot_symbols) for _ in range(3)]
        result_string = "".join(result)
        
        # Check for win
        payout = self.slot_payouts.get(result_string, 0)
        
        # Create result display
        slot_display = f"""
┏━━━━━━━━━━━━━┓
┃  🎰 SLOTS  🎰  ┃
┣━━━━━━━━━━━━━┫
┃  {result[0]} ┃ {result[1]} ┃ {result[2]}  ┃
┗━━━━━━━━━━━━━┛
        """
        
        if payout > 0:
            embed = discord.Embed(
                title="🎰 Slots Machine",
                description=f"{slot_display}\n\n🎉 **WINNER!** 🎉\nYou won **{payout}** coins!",
                color=0xffd700
            )
        else:
            # Check for partial matches
            if result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
                embed = discord.Embed(
                    title="🎰 Slots Machine",
                    description=f"{slot_display}\n\n😓 So close! Try again!",
                    color=0xffa726
                )
            else:
                embed = discord.Embed(
                    title="🎰 Slots Machine", 
                    description=f"{slot_display}\n\n💸 No match! Better luck next time!",
                    color=0xff6b6b
                )
        
        # Add payout table
        embed.add_field(
            name="💰 Payout Table",
            value="💎💎💎 = 100\n7️⃣7️⃣7️⃣ = 50\n⭐⭐⭐ = 25\n🍇🍇🍇 = 15\n🍊🍊🍊 = 10\n🍋🍋🍋 = 8\n🍒🍒🍒 = 5",
            inline=True
        )
        
        embed.set_footer(text=f"Played by {ctx.author.display_name}")
        await ctx.send(embed=embed)
        
    @commands.command(name='tictactoe', aliases=['ttt', 'tic'])
    async def tictactoe(self, ctx, opponent: discord.Member = None):
        if not opponent:
            embed = EmbedTemplates.error(
                "Missing Opponent",
                "Please mention someone to play against!\nExample: `.tictactoe @friend`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if opponent.bot:
            embed = EmbedTemplates.error(
                "Invalid Opponent",
                "You can't play against bots!",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if opponent == ctx.author:
            embed = EmbedTemplates.error(
                "Invalid Opponent",
                "You can't play against yourself!",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
        
        # Check if either player is already in a game
        if ctx.author.id in self.tictactoe_games or opponent.id in self.tictactoe_games:
            embed = EmbedTemplates.error(
                "Game In Progress",
                "One of you is already in a game! Finish that first.",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
        
        # Create game
        game_data = {
            'board': ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'],
            'player1': ctx.author,
            'player2': opponent,
            'current_player': ctx.author,
            'symbol': {'X': '❌', 'O': '⭕'}
        }
        
        self.tictactoe_games[ctx.author.id] = game_data
        self.tictactoe_games[opponent.id] = game_data
        
        def format_board(board):
            return f"""
┏━━━┳━━━┳━━━┓
┃ {board[0]} ┃ {board[1]} ┃ {board[2]} ┃
┣━━━╋━━━╋━━━┫
┃ {board[3]} ┃ {board[4]} ┃ {board[5]} ┃
┣━━━╋━━━╋━━━┫
┃ {board[6]} ┃ {board[7]} ┃ {board[8]} ┃
┗━━━┻━━━┻━━━┛
            """
        
        embed = discord.Embed(
            title="⭕ Tic Tac Toe ❌",
            description=f"{format_board(game_data['board'])}\n\n{ctx.author.mention} (❌) vs {opponent.mention} (⭕)\n\n🎯 {ctx.author.mention}'s turn!",
            color=0x9b59b6
        )
        embed.set_footer(text="React with the number (1-9) to make your move!")
        
        message = await ctx.send(embed=embed)
        
        # Add number reactions
        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
        for emoji in number_emojis:
            await message.add_reaction(emoji)
        
        def check_winner(board):
            # Check rows, columns, and diagonals
            win_patterns = [
                [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
                [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
                [0, 4, 8], [2, 4, 6]              # diagonals
            ]
            
            for pattern in win_patterns:
                if board[pattern[0]] == board[pattern[1]] == board[pattern[2]] and board[pattern[0]] in ['❌', '⭕']:
                    return board[pattern[0]]
            return None
        
        def check_tie(board):
            return all(cell in ['❌', '⭕'] for cell in board)
        
        def game_check(reaction, user):
            return (user == game_data['current_player'] and 
                   str(reaction.emoji) in number_emojis and 
                   reaction.message.id == message.id)
        
        # Game loop
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=game_check)
                
                # Get move position
                move = number_emojis.index(str(reaction.emoji))
                
                # Check if position is valid
                if game_data['board'][move] in ['❌', '⭕']:
                    continue  # Invalid move, wait for another
                
                # Make move
                current_symbol = '❌' if user == game_data['player1'] else '⭕'
                game_data['board'][move] = current_symbol
                
                # Check for winner
                winner = check_winner(game_data['board'])
                if winner:
                    winner_player = game_data['player1'] if winner == '❌' else game_data['player2']
                    embed = discord.Embed(
                        title="🎉 Game Over!",
                        description=f"{format_board(game_data['board'])}\n\n🏆 **{winner_player.mention} wins!**",
                        color=0x4ecdc4
                    )
                    await ctx.send(embed=embed)
                    del self.tictactoe_games[ctx.author.id]
                    del self.tictactoe_games[opponent.id]
                    return
                
                # Check for tie
                if check_tie(game_data['board']):
                    embed = discord.Embed(
                        title="🤝 Game Over!",
                        description=f"{format_board(game_data['board'])}\n\n🤝 **It's a tie!**",
                        color=0xffa726
                    )
                    await ctx.send(embed=embed)
                    del self.tictactoe_games[ctx.author.id]
                    del self.tictactoe_games[opponent.id]
                    return
                
                # Switch players
                game_data['current_player'] = game_data['player2'] if user == game_data['player1'] else game_data['player1']
                
                # Update board
                embed = discord.Embed(
                    title="⭕ Tic Tac Toe ❌",
                    description=f"{format_board(game_data['board'])}\n\n{ctx.author.mention} (❌) vs {opponent.mention} (⭕)\n\n🎯 {game_data['current_player'].mention}'s turn!",
                    color=0x9b59b6
                )
                embed.set_footer(text="React with the number (1-9) to make your move!")
                await ctx.send(embed=embed)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⏰ Game Timeout!",
                    description="The game has been cancelled due to inactivity.",
                    color=0xffa726
                )
                await ctx.send(embed=embed)
                if ctx.author.id in self.tictactoe_games:
                    del self.tictactoe_games[ctx.author.id]
                if opponent.id in self.tictactoe_games:
                    del self.tictactoe_games[opponent.id]
                return
                
    @commands.command(name='challenge')
    async def challenge(self, ctx, opponent: discord.Member, game: str = None):
        if not opponent:
            embed = EmbedTemplates.error(
                "Missing Opponent",
                "Please mention someone to challenge!\nExample: `.challenge @friend rps`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if not game:
            embed = EmbedTemplates.error(
                "Missing Game",
                "Please specify a game!\nAvailable: `rps`, `blackjack`, `tictactoe`\nExample: `.challenge @friend rps`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        if opponent.bot:
            embed = EmbedTemplates.error("Invalid Opponent", "You can't challenge bots!", ctx.author)
            await ctx.send(embed=embed)
            return
            
        if opponent == ctx.author:
            embed = EmbedTemplates.error("Invalid Opponent", "You can't challenge yourself!", ctx.author)
            await ctx.send(embed=embed)
            return
            
        game = game.lower()
        valid_games = ['rps', 'rockpaperscissors', 'blackjack', 'bj', '21', 'tictactoe', 'ttt', 'tic']
        
        if game not in valid_games:
            embed = EmbedTemplates.error(
                "Invalid Game",
                "Available challenge games: `rps`, `blackjack`, `tictactoe`",
                ctx.author
            )
            await ctx.send(embed=embed)
            return
            
        # Normalize game name
        if game in ['rps', 'rockpaperscissors']:
            game_name = "Rock Paper Scissors"
            game_cmd = "rps"
        elif game in ['blackjack', 'bj', '21']:
            game_name = "Blackjack"
            game_cmd = "blackjack" 
        elif game in ['tictactoe', 'ttt', 'tic']:
            game_name = "Tic Tac Toe"
            game_cmd = "tictactoe"
            
        embed = discord.Embed(
            title="🎮 Game Challenge",
            description=f"{ctx.author.mention} challenges {opponent.mention} to **{game_name}**!\n\n{opponent.mention}, react with ✅ to accept or ❌ to decline",
            color=0x5865f2
        )
        
        message = await ctx.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        
        def check(reaction, user):
            return (user == opponent and 
                   str(reaction.emoji) in ['✅', '❌'] and 
                   reaction.message.id == message.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '✅':
                embed = discord.Embed(
                    title="🎉 Challenge Accepted!",
                    description=f"{opponent.mention} accepted! Starting **{game_name}**...\n\nUse `.{game_cmd}` to begin!",
                    color=0x4ecdc4
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="😔 Challenge Declined",
                    description=f"{opponent.mention} declined the challenge.",
                    color=0xff6b6b
                )
                await ctx.send(embed=embed)
                
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Challenge Expired",
                description=f"{opponent.mention} didn't respond in time.",
                color=0xffa726
            )
            await ctx.send(embed=embed)

    # Error handlers
    @number_guess.error
    async def number_guess_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = EmbedTemplates.error(
                "Invalid Number",
                "Please enter a valid number!\nExample: `.guess 42`",
                ctx.author
            )
            await ctx.send(embed=embed)
            
    @dice_roll.error
    async def dice_roll_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = EmbedTemplates.error(
                "Invalid Dice Size",
                "Please enter a valid number for dice sides!\nExample: `.dice 20`",
                ctx.author
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Games(bot))