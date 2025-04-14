import random
import asyncio
import discord
from discord.ext import commands
import datetime
import os
from dotenv import load_dotenv
import pyjokes
import ctypes
import nacl
import requests
from bs4 import BeautifulSoup
import aiohttp

# Load environment variables
load_dotenv()

# Bot configuration
PREFIX = '~'
intents = discord.Intents.default()
intents.members = True  # Enable member intents to access member information
intents.message_content = True  # Enable message content intent
intents.guilds = True  # Make sure guild intent is enabled
intents.messages = True  # Make sure messages intent is enabled

# Initialize bot with prefix and intents
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Superfight game data
ATTRIBUTES = [
    "Armed with a slimeball launcher", "In handcuffs", "On a hoverboard", "Armed with a taser",
    "Tied to a bed", "Has super strength", "In Dumbledore's robe", "Flying a tie advanced", 
    "In full beskar", "With the one ring", "Wearing a tricorn hat", "Has one eye",
    "Had an hour to set up the battlefield beforehand", "With a compound bow and 5 arrows",
    "Has the infinity gauntlet with the time stone, space stone, and reality stone",
    "Wearing an explosive bonnet", "Has the power of teleportation", "With a dwarven thrower",
    "Has one eye", "With an army of jesters", "On a segway", 
    "Magically suspended upside down in midair", "Armed with an emotion ray",
    "With an apple on your head", "Invisible", "Cry's cash", "Riding an immortal pig",
    "On a fainting goat", "In a mech suit", "Armed with a cannon and unlimited cannonballs", 
    "Armed with a pulse rifle", "Riding an insane dragon with a grudge against the opponent",
    "3 of them", "50 of them", "100 of them", "Wearing a cap of stupidity", 
    "With the largest brain ever", "Will faint from fright if it sees a tree",
    "Made out of animated lego's", "With zeus's lightning bolt", "With the palantir", 
    "Can speak to birds", "Has a head to big for its body", "Is as large as godzilla",
    "Constantly shedding cat hair", "In a flying car", "Armed with a mailbox", 
    "Armed with a duck crossing sign", "With a purple spud", "Suffers from extreme flatulence",
    "Is the ugliest person in the world", "Shoots fireballs", "Can Use the force", 
    "Can Steal an opponent's attributes", "In the razor crest", "Tied up in used dental floss",
    "Is constantly dancing the robot", "Made of sand", "Can change corporeality at will", 
    "Is foaming at the mouth", "Swinging a shark on a chain", "Holding a don't touch button",
    "Had plastic surgery", "The size of a mouse", "That makes chicken noises when they talk", 
    "Driving the batmobile", "Armed with unlimited tnt", "Wielding the sword of summer",
    "With a catapult and unlimited pies", "With a rod that can be any projectile weapon in the multiverse",
    "Sucking on a push pop", "Balancing on a tightrope", "Hooked up to a lie detector", 
    "Holding a chapstick", "Sitting on a couch", "With a glue stick",
    "On whom it is constantly raining, though it is raining nowhere else", 
    "Looking down the barrel of a squirt gun", "With telepathy", "Who can fly",
    "With a ferret that sings twinkle little star everytime it hears a noise", 
    "On a bicycle", "Named sue", "With facepaints", "Eating a potato", "In a rocking chair",
    "Who can summon meteor strikes at will"
]

CHARACTERS = [
    "Pikachu", "Darth plagueis", "A killer bee swarm", "A tusken raider", "Soundwave", 
    "A dog", "A Dracolich", "Baby yoda", "A jewel thief", "Superman", "A t-rex", "A shopkin", 
    "A tv show character of your choice", "A park ranger", "Sauron", "A porg", 
    "A living statue of benjamin franklin", "The one and only Ivan", "Bossk", 
    "A librarian in a fuzzy purple hat", "A french butler", "A djinn", "Spiderman", 
    "Andre the giant", "Elrond", "Manbat", "R2d2", "An astronaut", "Dumbledore", 
    "A goat", "Count Dracula", "Will Treaty", "Boba Fett", 
    "A video game character of your choice", "A satyr", "King Arthur", "Bad cop", 
    "A pile of dynamite", "Optimus prime", "Lobelia Sackville-Baggins", "Tacocat", 
    "Gandalf", "Attack rag doll", "Elsa from frozen", "A teletubby", "Blackbeard", 
    "John Cena", "Justin Bieber", "Alcatraz prison guard", "Davy Jones", "C-3P0", 
    "The KRACKEN!", "A micromanager", "A Monster-Trucker", "Polly the parrot", 
    "A boy-band", "A surfer", "An airplane pilot", "A wyvern", "billybobjoe"
]

# Active games dictionary to track games in progress
active_games = {}

# Game states
WAITING_FOR_PLAYERS = 0
IN_PROGRESS = 1
VOTING = 2

class SuperfightGame:
    def __init__(self, channel_id, host_id):
        self.channel_id = channel_id
        self.host_id = host_id
        self.players = []  # List of player IDs
        self.state = WAITING_FOR_PLAYERS
        self.current_round = 0
        self.max_rounds = 3
        self.player_cards = {}  # Map player_id -> [character, attribute1, attribute2]
        self.votes = {}  # Map voter_id -> voted_player_id
        self.round_winners = []

    def add_player(self, player_id):
        if player_id not in self.players and len(self.players) < 8:
            self.players.append(player_id)
            return True
        return False

    def remove_player(self, player_id):
        if player_id in self.players:
            self.players.remove(player_id)
            return True
        return False

    def deal_cards(self):
        for player_id in self.players:
            character = random.choice(CHARACTERS)
            attribute1 = random.choice(ATTRIBUTES)
            attribute2 = random.choice(ATTRIBUTES)
            
            # Make sure attributes are different
            while attribute1 == attribute2:
                attribute2 = random.choice(ATTRIBUTES)
                
            self.player_cards[player_id] = [character, attribute1, attribute2]

    def get_player_card_string(self, player_id):
        if player_id not in self.player_cards:
            return "No card assigned"
            
        card = self.player_cards[player_id]
        return f"**Character:** {card[0]}\n**Attributes:** {card[1]}, {card[2]}"

    def reset_votes(self):
        self.votes = {}

    def add_vote(self, voter_id, voted_for_id):
        self.votes[voter_id] = voted_for_id
        return len(self.votes)

    def get_vote_results(self):
        # Count votes for each player
        vote_counts = {}
        for voted_for_id in self.votes.values():
            if voted_for_id in vote_counts:
                vote_counts[voted_for_id] += 1
            else:
                vote_counts[voted_for_id] = 1
                
        # Find winners (could be ties)
        max_votes = 0
        winners = []
        
        for player_id, count in vote_counts.items():
            if count > max_votes:
                max_votes = count
                winners = [player_id]
            elif count == max_votes:
                winners.append(player_id)
                
        return winners, vote_counts

@bot.command(name='superfight', aliases=['sf'])
async def superfight(ctx):
    """Start a game of Superfight!"""
    channel_id = ctx.channel.id
    
    # Check if a game is already running in this channel
    if channel_id in active_games:
        await ctx.send("A game is already in progress in this channel!")
        return
    
    # Create a new game
    game = SuperfightGame(channel_id, ctx.author.id)
    active_games[channel_id] = game
    
    # Add the host as the first player
    game.add_player(ctx.author.id)
    
    # Create an embed for the game announcement
    embed = discord.Embed(
        title="🥊 SUPERFIGHT! 🥊",
        description=(
            "A new Superfight game has started!\n\n"
            "**How to play:**\n"
            "1. Players join using `~sfjoin`\n"
            "2. Each player gets a character and 2 attributes\n"
            "3. Players take turns arguing why their fighter would win\n"
            "4. Everyone votes for the winner\n\n"
            "The host can start the game with `~sfstart` once everyone has joined."
        ),
        color=discord.Color.from_str("#FF9900")
    )
    
    embed.add_field(name="Host", value=ctx.author.mention, inline=True)
    embed.add_field(name="Players", value=f"1/{game.max_rounds*2}", inline=True)
    embed.set_footer(text="Game ID: " + str(channel_id))
    
    await ctx.send(embed=embed)

@bot.command(name='sfjoin')
async def superfight_join(ctx):
    """Join an ongoing Superfight game in this channel"""
    channel_id = ctx.channel.id
    
    # Check if a game exists in this channel
    if channel_id not in active_games:
        await ctx.send("No Superfight game is active in this channel. Start one with `~superfight`!")
        return
    
    game = active_games[channel_id]
    
    # Check if the game is still accepting players
    if game.state != WAITING_FOR_PLAYERS:
        await ctx.send("This game has already started. Wait for the next one!")
        return
    
    # Add the player
    if game.add_player(ctx.author.id):
        embed = discord.Embed(
            title="Player Joined",
            description=f"{ctx.author.mention} has joined the Superfight match!",
            color=discord.Color.green()
        )
        embed.add_field(name="Players", value=f"{len(game.players)}/{game.max_rounds*2}", inline=True)
        await ctx.send(embed=embed)
    else:
        if ctx.author.id in game.players:
            await ctx.send("You're already in this game!")
        else:
            await ctx.send("The game is full!")

@bot.command(name='sfleave')
async def superfight_leave(ctx):
    """Leave a Superfight game you've joined"""
    channel_id = ctx.channel.id
    
    # Check if a game exists in this channel
    if channel_id not in active_games:
        await ctx.send("No Superfight game is active in this channel.")
        return
    
    game = active_games[channel_id]
    
    # Check if the game hasn't started yet
    if game.state != WAITING_FOR_PLAYERS:
        await ctx.send("The game has already started. You can't leave now!")
        return
    
    # Remove the player
    if game.remove_player(ctx.author.id):
        await ctx.send(f"{ctx.author.mention} has left the Superfight match.")
        
        # If the host leaves, end the game
        if ctx.author.id == game.host_id:
            await ctx.send("The host has left. The game has been cancelled.")
            del active_games[channel_id]
    else:
        await ctx.send("You're not in this game!")

@bot.command(name='sfstart')
async def superfight_start(ctx):
    """Start a Superfight game that's accepting players"""
    channel_id = ctx.channel.id
    
    # Check if a game exists in this channel
    if channel_id not in active_games:
        await ctx.send("No Superfight game is active in this channel. Start one with `~superfight`!")
        return
    
    game = active_games[channel_id]
    
    # Check if the user is the host
    if ctx.author.id != game.host_id:
        await ctx.send("Only the host can start the game!")
        return
    
    # Check if the game is still in the waiting state
    if game.state != WAITING_FOR_PLAYERS:
        await ctx.send("The game has already started!")
        return
    
    # Check if we have at least 2 players
    if len(game.players) < 2:
        await ctx.send("You need at least 2 players to start a game!")
        return
    
    # Start the game
    game.state = IN_PROGRESS
    
    # Deal cards to players
    game.deal_cards()
    
    # Announce the game has started
    embed = discord.Embed(
        title="🥊 SUPERFIGHT BEGINS! 🥊",
        description=f"The battle begins with {len(game.players)} fighters!",
        color=discord.Color.from_str("#FF9900")
    )
    
    await ctx.send(embed=embed)
    
    # Send private messages to each player with their cards
    for player_id in game.players:
        player = await bot.fetch_user(player_id)
        if player:
            card_info = game.get_player_card_string(player_id)
            player_embed = discord.Embed(
                title="Your Superfight Card",
                description=f"Here is your fighter for the Superfight match:\n\n{card_info}",
                color=discord.Color.blue()
            )
            player_embed.set_footer(text="Argue why your fighter would win when it's your turn!")
            
            try:
                await player.send(embed=player_embed)
            except discord.Forbidden:
                await ctx.send(f"{player.mention} I couldn't send you a DM with your card! Please check your privacy settings.")
    
    # Start the first round
    await start_round(ctx, game)

async def start_round(ctx, game):
    """Start a new round of the game"""
    game.current_round += 1
    
    if game.current_round > game.max_rounds:
        # Game is over, announce the winner
        await end_game(ctx, game)
        return
    
    # Determine which players are competing this round
    if len(game.players) >= 2:
        # If we have enough players, select two that haven't been selected yet
        # This is simplified - ideally you'd track which players have already competed
        player1_idx = (game.current_round * 2 - 2) % len(game.players)
        player2_idx = (game.current_round * 2 - 1) % len(game.players)
        
        if player1_idx == player2_idx:  # In case we have an odd number
            player2_idx = (player2_idx + 1) % len(game.players)
            
        player1_id = game.players[player1_idx]
        player2_id = game.players[player2_idx]
        
        player1 = await bot.fetch_user(player1_id)
        player2 = await bot.fetch_user(player2_id)
        
        # Announce the matchup
        embed = discord.Embed(
            title=f"Round {game.current_round} Fight!",
            description=f"This round's matchup:\n\n{player1.mention} VS {player2.mention}",
            color=discord.Color.from_str("#FF9900")
        )
        
        # Add the fighter cards
        embed.add_field(
            name=f"{player1.name}'s Fighter",
            value=game.get_player_card_string(player1_id),
            inline=False
        )
        
        embed.add_field(
            name=f"{player2.name}'s Fighter",
            value=game.get_player_card_string(player2_id),
            inline=False
        )
        
        embed.add_field(
            name="Instructions",
            value=(
                f"1. {player1.mention} has 2 minutes to argue why they would win\n"
                f"2. {player2.mention} then has 2 minutes to argue why they would win\n"
                f"3. Everyone will vote using the `~sfvote @player` command\n"
                f"4. The host can force the vote to end with `~sfendvote`"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Set a timer for the voting phase
        await asyncio.sleep(240)  # 4 minutes for arguments
        
        # Start voting phase
        game.state = VOTING
        game.reset_votes()
        
        vote_embed = discord.Embed(
            title="Time to Vote!",
            description=(
                f"Arguments are over! Who won?\n\n"
                f"Vote using `~sfvote @player`\n\n"
                f"Options:\n"
                f"1️⃣ {player1.mention}\n"
                f"2️⃣ {player2.mention}"
            ),
            color=discord.Color.from_str("#FF9900")
        )
        
        await ctx.send(embed=vote_embed)
        
        # Set a timer for the voting phase
        await asyncio.sleep(60)  # 1 minute for voting
        
        # End voting and announce results
        await end_voting(ctx, game, [player1_id, player2_id])
    else:
        await ctx.send("Not enough players to continue!")
        del active_games[game.channel_id]

@bot.command(name='sfvote')
async def superfight_vote(ctx, player: discord.Member):
    """Vote for a player in the current Superfight round"""
    channel_id = ctx.channel.id
    
    # Check if a game exists in this channel
    if channel_id not in active_games:
        await ctx.send("No Superfight game is active in this channel.")
        return
    
    game = active_games[channel_id]
    
    # Check if the game is in voting phase
    if game.state != VOTING:
        await ctx.send("Voting is not active right now!")
        return
    
    # Check if the voted player is in the game
    if player.id not in game.players:
        await ctx.send("That player is not in this game!")
        return
    
    # Record the vote
    game.add_vote(ctx.author.id, player.id)
    
    # Confirm the vote
    await ctx.message.add_reaction('👍')

@bot.command(name='sfendvote')
async def superfight_end_vote(ctx):
    """End the voting phase early (host only)"""
    channel_id = ctx.channel.id
    
    # Check if a game exists in this channel
    if channel_id not in active_games:
        await ctx.send("No Superfight game is active in this channel.")
        return
    
    game = active_games[channel_id]
    
    # Check if the user is the host
    if ctx.author.id != game.host_id:
        await ctx.send("Only the host can end voting early!")
        return
    
    # Check if the game is in voting phase
    if game.state != VOTING:
        await ctx.send("Voting is not active right now!")
        return
    
    # Get the players for this round
    player1_idx = (game.current_round * 2 - 2) % len(game.players)
    player2_idx = (game.current_round * 2 - 1) % len(game.players)
    
    if player1_idx == player2_idx:  # In case we have an odd number
        player2_idx = (player2_idx + 1) % len(game.players)
        
    player1_id = game.players[player1_idx]
    player2_id = game.players[player2_idx]
    
    # End voting
    await end_voting(ctx, game, [player1_id, player2_id])

async def end_voting(ctx, game, round_players):
    """End the voting phase and announce results"""
    # Get vote results
    winners, vote_counts = game.get_vote_results()
    
    # Prepare the results message
    results_embed = discord.Embed(
        title="Round Results",
        color=discord.Color.gold()
    )
    
    # Get vote counts for each player
    vote_text = ""
    for player_id in round_players:
        player = await bot.fetch_user(player_id)
        count = vote_counts.get(player_id, 0)
        vote_text += f"{player.mention}: {count} vote(s)\n"
    
    results_embed.add_field(name="Votes", value=vote_text or "No votes cast!", inline=False)
    
    # Announce winner(s)
    if winners:
        winner_mentions = []
        for winner_id in winners:
            winner = await bot.fetch_user(winner_id)
            winner_mentions.append(winner.mention)
            game.round_winners.append(winner_id)
        
        if len(winner_mentions) == 1:
            results_embed.description = f"The winner is {winner_mentions[0]}!"
        else:
            results_embed.description = f"It's a tie between {' and '.join(winner_mentions)}!"
    else:
        results_embed.description = "No one received any votes!"
    
    await ctx.send(embed=results_embed)
    
    # Reset for next round
    game.state = IN_PROGRESS
    
    # Start the next round
    await asyncio.sleep(5)
    await start_round(ctx, game)

async def end_game(ctx, game):
    """End the game and announce the final winner"""
    # Count how many rounds each player won
    win_counts = {}
    for winner_id in game.round_winners:
        if winner_id in win_counts:
            win_counts[winner_id] += 1
        else:
            win_counts[winner_id] = 1
    
    # Find the player(s) with the most round wins
    most_wins = 0
    final_winners = []
    
    for player_id, wins in win_counts.items():
        if wins > most_wins:
            most_wins = wins
            final_winners = [player_id]
        elif wins == most_wins:
            final_winners.append(player_id)
    
    # Create the final results embed
    final_embed = discord.Embed(
        title="🏆 SUPERFIGHT CHAMPION 🏆",
        color=discord.Color.gold()
    )
    
    if final_winners:
        winner_mentions = []
        for winner_id in final_winners:
            winner = await bot.fetch_user(winner_id)
            winner_mentions.append(winner.mention)
        
        if len(winner_mentions) == 1:
            final_embed.description = f"The champion is {winner_mentions[0]} with {most_wins} round win(s)!"
        else:
            final_embed.description = f"It's a tie between {' and '.join(winner_mentions)}, each with {most_wins} round win(s)!"
    else:
        final_embed.description = "No clear winner! Everyone's a champion today!"
    
    # Add all players' scores
    scores_text = ""
    for player_id in game.players:
        player = await bot.fetch_user(player_id)
        wins = win_counts.get(player_id, 0)
        scores_text += f"{player.mention}: {wins} round win(s)\n"
    
    final_embed.add_field(name="Final Scores", value=scores_text, inline=False)
    final_embed.set_footer(text="Thanks for playing Superfight!")
    
    await ctx.send(embed=final_embed)
    
    # Remove the game from active games
    del active_games[game.channel_id]

@bot.command(name='sfcancel')
async def superfight_cancel(ctx):
    """Cancel an ongoing Superfight game (host only)"""
    channel_id = ctx.channel.id
    
    # Check if a game exists in this channel
    if channel_id not in active_games:
        await ctx.send("No Superfight game is active in this channel.")
        return
    
    game = active_games[channel_id]
    
    # Check if the user is the host
    if ctx.author.id != game.host_id:
        await ctx.send("Only the host can cancel the game!")
        return
    
    # Cancel the game
    del active_games[channel_id]
    
    await ctx.send("The Superfight game has been cancelled.")

@bot.command(name='sfhelp')
async def superfight_help(ctx):
    """Show help for Superfight commands"""
    help_embed = discord.Embed(
        title="Superfight Help",
        description="Here are the commands for playing Superfight:",
        color=discord.Color.blue()
    )
    
    help_embed.add_field(
        name="~superfight (or ~sf)",
        value="Start a new Superfight game in the current channel",
        inline=False
    )
    
    help_embed.add_field(
        name="~sfjoin",
        value="Join an ongoing Superfight game",
        inline=False
    )
    
    help_embed.add_field(
        name="~sfleave",
        value="Leave a Superfight game you've joined (before it starts)",
        inline=False
    )
    
    help_embed.add_field(
        name="~sfstart",
        value="Start the game (host only)",
        inline=False
    )
    
    help_embed.add_field(
        name="~sfvote @player",
        value="Vote for a player during the voting phase",
        inline=False
    )
    
    help_embed.add_field(
        name="~sfendvote",
        value="End the voting phase early (host only)",
        inline=False
    )
    
    help_embed.add_field(
        name="~sfcancel",
        value="Cancel the current game (host only)",
        inline=False
    )
    
    await ctx.send(embed=help_embed)