import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import asyncio
import sys
import os
import datetime
from queue import Queue
import discord
from discord.ext import commands
import requests
from PIL import Image, ImageTk
from io import BytesIO

# Global message queue for thread communication
message_queue = Queue()

# Global bot instance - this will be set by your main bot file
bot = None

class ConsoleRedirector:
    """Redirects stdout/stderr to the GUI console"""
    def __init__(self, queue):
        self.queue = queue

    def write(self, message):
        if message.strip():
            self.queue.put(message)

    def flush(self):
        pass

class TerminalNavigator:
    """Handles terminal-style navigation through Discord servers and channels"""
    def __init__(self):
        self.current_guild = None
        self.current_channel = None
        self.path_stack = []
        
    def get_current_path(self):
        """Returns the current path string"""
        if not self.current_guild:
            return "~"
        elif not self.current_channel:
            return f"~/{self.current_guild.name}"
        else:
            return f"~/{self.current_guild.name}/{self.current_channel.name}"
    
    def cd(self, path, bot_instance):
        """Change directory - navigate through servers/channels"""
        if not bot_instance or not bot_instance.guilds:
            return "Bot not connected to any servers"
            
        if path == "~" or path == "/":
            self.current_guild = None
            self.current_channel = None
            return f"Changed to root directory"
            
        if path == "..":
            if self.current_channel:
                self.current_channel = None
                return f"Changed to server: {self.current_guild.name}"
            elif self.current_guild:
                self.current_guild = None
                return "Changed to root directory"
            else:
                return "Already at root directory"
        
        # If we're at root, look for server
        if not self.current_guild:
            guild = discord.utils.find(lambda g: g.name.lower() == path.lower(), bot_instance.guilds)
            if guild:
                self.current_guild = guild
                self.current_channel = None
                return f"Changed to server: {guild.name}"
            else:
                return f"Server '{path}' not found"
        
        # If we're in a server, look for channel
        elif not self.current_channel:
            channel = discord.utils.find(
                lambda c: c.name.lower() == path.lower() and hasattr(c, 'send'), 
                self.current_guild.channels
            )
            if channel:
                self.current_channel = channel
                return f"Changed to channel: {channel.name}"
            else:
                return f"Channel '{path}' not found in {self.current_guild.name}"
        
        return "Cannot navigate deeper than channel level"
    
    def ls(self, bot_instance):
        """List current directory contents"""
        if not bot_instance or not bot_instance.guilds:
            return "Bot not connected to any servers"
            
        if not self.current_guild:
            # List all servers
            servers = [f"📁 {guild.name} ({len(guild.channels)} channels)" for guild in bot_instance.guilds]
            return "Available servers:\n" + "\n".join(servers)
        
        elif not self.current_channel:
            # List channels in current server
            text_channels = [f"💬 {ch.name}" for ch in self.current_guild.text_channels]
            voice_channels = [f"🔊 {ch.name}" for ch in self.current_guild.voice_channels]
            all_channels = text_channels + voice_channels
            return f"Channels in {self.current_guild.name}:\n" + "\n".join(all_channels)
        
        else:
            # We're in a channel, show channel info
            return f"Current channel: {self.current_channel.name}\n" \
                   f"Type: {type(self.current_channel).__name__}\n" \
                   f"Topic: {getattr(self.current_channel, 'topic', 'None')}"

def load_image_from_url(url, size=(32, 32)):
    """Load and resize an image from URL"""
    try:
        response = requests.get(url, timeout=5)
        img = Image.open(BytesIO(response.content))
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def set_bot_instance(bot_instance):
    """Set the bot instance from your main bot file"""
    global bot
    bot = bot_instance
    
    # Store original event handlers to avoid overriding them
    original_on_ready = getattr(bot, 'on_ready', None)
    original_on_guild_join = getattr(bot, 'on_guild_join', None)
    original_on_guild_remove = getattr(bot, 'on_guild_remove', None)
    original_on_message = getattr(bot, 'on_message', None)
    original_on_disconnect = getattr(bot, 'on_disconnect', None)
    original_on_resumed = getattr(bot, 'on_resumed', None)
    
    # Create wrapper functions that call both original and dashboard handlers
    async def dashboard_on_ready():
        if original_on_ready:
            await original_on_ready()
        
        message_queue.put(f"✅ Bot logged in as {bot.user.name}")
        message_queue.put(f"Connected to {len(bot.guilds)} servers")
        
        # Send structured status update
        message_queue.put({
            "type": "status_update",
            "online": True
        })
        
        # Send statistics update
        stats = {
            "servers": len(bot.guilds),
            "channels": sum(len(guild.channels) for guild in bot.guilds),
            "users": sum(guild.member_count or 0 for guild in bot.guilds),
            "commands": 0
        }
        message_queue.put({
            "type": "stats_update",
            "data": stats
        })
    
    async def dashboard_on_guild_join(guild):
        if original_on_guild_join:
            await original_on_guild_join(guild)
        message_queue.put(f"📥 Joined server: {guild.name} ({guild.member_count} members)")
        
    async def dashboard_on_guild_remove(guild):
        if original_on_guild_remove:
            await original_on_guild_remove(guild)
        message_queue.put(f"📤 Left server: {guild.name}")
        
    async def dashboard_on_message(message):
        if original_on_message:
            await original_on_message(message)
            
        if message.author == bot.user:
            return
            
        # Log commands being used
        if message.content.startswith(bot.command_prefix):
            message_queue.put(f"🔧 Command used by {message.author.name} in #{message.channel.name}: {message.content}")
    
    async def dashboard_on_disconnect():
        if original_on_disconnect:
            await original_on_disconnect()
        message_queue.put("⚠️ Bot disconnected from Discord")
        message_queue.put({
            "type": "status_update", 
            "online": False
        })
    
    async def dashboard_on_resumed():
        if original_on_resumed:
            await original_on_resumed()
        message_queue.put("🔄 Bot reconnected to Discord")
        message_queue.put({
            "type": "status_update",
            "online": True
        })
    
    # Replace event handlers with dashboard-aware versions
    bot.on_ready = dashboard_on_ready
    bot.on_guild_join = dashboard_on_guild_join
    bot.on_guild_remove = dashboard_on_guild_remove
    bot.on_message = dashboard_on_message
    bot.on_disconnect = dashboard_on_disconnect
    bot.on_resumed = dashboard_on_resumed

class BotDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Osmium Bot Dashboard")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 600)
        
        # Terminal navigator
        self.navigator = TerminalNavigator()
        
        # Command history
        self.command_history = []
        self.history_index = 0
        
        # Theme colors - using original color scheme
        self.colors = {
            'bg_primary': '#222222',      # bg_darker
            'bg_secondary': '#2D2D2D',    # bg_dark
            'bg_tertiary': '#3D3D3D',     # Slightly lighter than bg_dark
            'accent': '#2a3ffa',          # Original accent color
            'accent_hover': '#3D5AFD',    # Secondary accent
            'text_primary': '#E0E0E0',    # Original text color
            'text_secondary': '#A0A0A0',  # Slightly dimmed text
            'success': '#4CAF50',         # Green
            'warning': '#FF9800',         # Orange
            'error': '#F44336',           # Red
            'border': '#404040'           # Border color
        }
        
        self.setup_ui()
        self.setup_bindings()
        
        # Start queue checking
        self.check_queue()
        
        # Initial status
        self.print_to_console("🚀 Osmium Bot Dashboard initialized")
        self.print_to_console("💡 Use 'help' for available commands")

    def setup_ui(self):
        """Setup the main UI layout"""
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1, minsize=350)
        self.root.columnconfigure(1, weight=2, minsize=500)
        self.root.rowconfigure(0, weight=1)
        
        # Create left sidebar (dashboard)
        self.create_sidebar()
        
        # Create right panel (terminal console)
        self.create_console_panel()
        
    def create_sidebar(self):
        """Create the left sidebar with dashboard controls"""
        sidebar = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        sidebar.columnconfigure(0, weight=1)
        
        # Header
        header_frame = tk.Frame(sidebar, bg=self.colors['accent'], height=60)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 1))
        header_frame.grid_propagate(False)
        
        title_label = tk.Label(
            header_frame, text="OSMIUM", 
            fg='white', bg=self.colors['accent'],
            font=('JetBrains Mono', 20, 'bold')
        )
        title_label.pack(expand=True)
        
        # Scrollable content
        canvas = tk.Canvas(sidebar, bg=self.colors['bg_secondary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(sidebar, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_secondary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")
        sidebar.rowconfigure(1, weight=1)
        
        # Status Section
        self.create_status_section(scrollable_frame)
        
        # Statistics Section
        self.create_stats_section(scrollable_frame)
        
        # Server Icons Section
        self.create_servers_section(scrollable_frame)
        
        # Control Buttons Section
        self.create_controls_section(scrollable_frame)
        
    def create_status_section(self, parent):
        """Create bot status section"""
        section = self.create_section_frame(parent, "🤖 BOT STATUS")
        
        # Status indicator
        status_frame = tk.Frame(section, bg=self.colors['bg_secondary'])
        status_frame.pack(fill="x", padx=15, pady=5)
        
        self.status_dot = tk.Canvas(
            status_frame, width=12, height=12, 
            bg=self.colors['bg_secondary'], highlightthickness=0
        )
        self.status_dot.pack(side="left", pady=2)
        self.status_circle = self.status_dot.create_oval(2, 2, 10, 10, fill="#6c757d", outline="")
        
        self.status_label = tk.Label(
            status_frame, text="Connecting...",
            fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'],
            font=('JetBrains Mono', 10)
        )
        self.status_label.pack(side="left", padx=(8, 0))
        
    def create_stats_section(self, parent):
        """Create statistics section"""
        section = self.create_section_frame(parent, "📊 STATISTICS")
        
        stats_frame = tk.Frame(section, bg=self.colors['bg_secondary'])
        stats_frame.pack(fill="x", padx=15, pady=5)
        
        # Create stat rows
        self.stats = {}
        stat_items = [
            ("Servers", "servers"),
            ("Channels", "channels"), 
            ("Users", "users"),
            ("Commands", "commands")
        ]
        
        for i, (label, key) in enumerate(stat_items):
            row = tk.Frame(stats_frame, bg=self.colors['bg_secondary'])
            row.pack(fill="x", pady=2)
            
            tk.Label(
                row, text=f"{label}:",
                fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'],
                font=('JetBrains Mono', 9)
            ).pack(side="left")
            
            self.stats[key] = tk.Label(
                row, text="--",
                fg=self.colors['text_primary'], bg=self.colors['bg_secondary'],
                font=('JetBrains Mono', 9, 'bold')
            )
            self.stats[key].pack(side="right")
            
    def create_servers_section(self, parent):
        """Create server list section"""
        section = self.create_section_frame(parent, "🏠 SERVERS")
        
        # Server list frame
        self.servers_frame = tk.Frame(section, bg=self.colors['bg_secondary'])
        self.servers_frame.pack(fill="x", padx=15, pady=5)
        
    def create_controls_section(self, parent):
        """Create control buttons section"""
        section = self.create_section_frame(parent, "⚙️ CONTROLS")
        
        # Button configurations
        buttons = [
            ("🔄 Refresh Status", self.refresh_status, self.colors['accent']),
            ("📋 Clear Console", self.clear_console, self.colors['warning']),
            ("📊 Show Stats", self.show_detailed_stats, self.colors['success']),
            ("🚪 Disconnect Bot", self.disconnect_bot, self.colors['error'])
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                section, text=text, command=command,
                bg=color, fg='white',
                font=('JetBrains Mono', 10, 'bold'),
                relief='flat', padx=15, pady=8,
                cursor='hand2'
            )
            btn.pack(fill="x", padx=15, pady=3)
            
            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.lighten_color(color)))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))
            
    def create_console_panel(self):
        """Create the terminal console panel"""
        console_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        console_frame.grid(row=0, column=1, sticky="nsew")
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(1, weight=1)
        
        # Console header
        header = tk.Frame(console_frame, bg=self.colors['bg_tertiary'], height=40)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        
        tk.Label(
            header, text="TERMINAL CONSOLE",
            fg=self.colors['text_primary'], bg=self.colors['bg_tertiary'],
            font=('JetBrains Mono', 12, 'bold')
        ).pack(side="left", padx=15, pady=10)
        
        # Path indicator
        self.path_label = tk.Label(
            header, text="~",
            fg=self.colors['text_secondary'], bg=self.colors['bg_tertiary'],
            font=('JetBrains Mono', 10)
        )
        self.path_label.pack(side="right", padx=15, pady=10)
        
        # Console output
        self.console = scrolledtext.ScrolledText(
            console_frame,
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['accent'],
            selectbackground=self.colors['accent'],
            font=('JetBrains Mono', 10),
            relief='flat',
            state='disabled',
            wrap=tk.WORD
        )
        self.console.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)
        
        # Configure tags for colored output
        self.console.tag_config("error", foreground=self.colors['error'])
        self.console.tag_config("success", foreground=self.colors['success'])
        self.console.tag_config("warning", foreground=self.colors['warning'])
        self.console.tag_config("info", foreground=self.colors['accent'])
        self.console.tag_config("prompt", foreground=self.colors['accent'], font=('JetBrains Mono', 10, 'bold'))
        
        # Input frame
        input_frame = tk.Frame(console_frame, bg=self.colors['bg_tertiary'], height=50)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.grid_propagate(False)
        input_frame.columnconfigure(1, weight=1)
        
        # Prompt label
        self.prompt_label = tk.Label(
            input_frame, text="$ ",
            fg=self.colors['accent'], bg=self.colors['bg_tertiary'],
            font=('JetBrains Mono', 11, 'bold')
        )
        self.prompt_label.grid(row=0, column=0, padx=(15, 5), pady=15)
        
        # Command input
        self.command_entry = tk.Entry(
            input_frame,
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['accent'],
            relief='flat',
            font=('JetBrains Mono', 11),
            bd=0
        )
        self.command_entry.grid(row=0, column=1, sticky="ew", padx=(0, 15), pady=15)
        
    def create_section_frame(self, parent, title):
        """Create a styled section frame with title"""
        # Section container
        section = tk.Frame(parent, bg=self.colors['bg_secondary'])
        section.pack(fill="x", pady=(0, 10))
        
        # Title
        title_label = tk.Label(
            section, text=title,
            fg=self.colors['accent'], bg=self.colors['bg_secondary'],
            font=('JetBrains Mono', 11, 'bold')
        )
        title_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Separator line
        separator = tk.Frame(section, bg=self.colors['border'], height=1)
        separator.pack(fill="x", padx=15)
        
        return section
        
    def setup_bindings(self):
        """Setup keyboard bindings"""
        self.command_entry.bind("<Return>", self.execute_command)
        self.command_entry.bind("<Up>", self.history_up)
        self.command_entry.bind("<Down>", self.history_down)
        self.command_entry.bind("<Tab>", self.autocomplete)
        self.command_entry.focus_set()
        
    def execute_command(self, event=None):
        """Execute command from terminal input"""
        command = self.command_entry.get().strip()
        if not command:
            return
            
        # Add to history
        if command != (self.command_history[-1] if self.command_history else None):
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Clear input
        self.command_entry.delete(0, tk.END)
        
        # Show command in console
        self.print_to_console(f"$ {command}", "prompt")
        
        # Process command
        self.process_terminal_command(command)
        
    def process_terminal_command(self, command):
        """Process terminal-style commands"""
        global bot
        parts = command.split()
        cmd = parts[0].lower() if parts else ""
        
        if cmd == "help":
            help_text = """Available Commands:
• ls                    - List current directory contents
• cd <path>            - Change directory (server/channel)
• pwd                  - Show current path
• clear                - Clear console
• status               - Show bot status
• servers              - List all servers
• channels             - List channels in current server
• send <message>       - Send message to current channel
• <bot_command>        - Execute any bot command (e.g., ban, kick, help)
• !<bot_command>       - Execute bot command with prefix
• history              - Show command history
• exit                 - Disconnect bot

Bot Commands:
Once in a channel, you can execute any of your bot's commands directly:
• ban @user reason     - Ban a user
• kick @user reason    - Kick a user  
• help                 - Show bot's help
• Or any other command your bot supports"""
            self.print_to_console(help_text, "info")
            
        elif cmd == "ls":
            result = self.navigator.ls(bot)
            self.print_to_console(result)
            
        elif cmd == "cd":
            if len(parts) > 1:
                path = " ".join(parts[1:])
                result = self.navigator.cd(path, bot)
                self.print_to_console(result)
                self.update_path_display()
            else:
                self.print_to_console("Usage: cd <server_name|channel_name|..|~>")
                
        elif cmd == "pwd":
            self.print_to_console(self.navigator.get_current_path())
            
        elif cmd == "clear":
            self.clear_console()
            
        elif cmd == "status":
            self.refresh_status()
            
        elif cmd == "servers":
            if bot and bot.guilds:
                servers_list = "\n".join([f"• {guild.name} ({len(guild.channels)} channels)" 
                                        for guild in bot.guilds])
                self.print_to_console(f"Connected servers:\n{servers_list}")
            else:
                self.print_to_console("No servers available", "warning")
                
        elif cmd == "channels":
            if self.navigator.current_guild:
                channels = [f"• #{ch.name}" for ch in self.navigator.current_guild.text_channels]
                if channels:
                    self.print_to_console(f"Channels in {self.navigator.current_guild.name}:\n" + 
                                        "\n".join(channels))
                else:
                    self.print_to_console("No text channels available", "warning")
            else:
                self.print_to_console("Not in any server. Use 'cd <server_name>' first", "warning")
                
        elif cmd == "send":
            if len(parts) > 1:
                message = " ".join(parts[1:])
                self.send_message_to_channel(message)
            else:
                self.print_to_console("Usage: send <message>", "warning")
                
        elif cmd.startswith(bot.command_prefix if bot else "!"):
            # Handle bot commands directly
            if not self.navigator.current_channel:
                self.print_to_console("No channel selected. Use 'cd' to navigate to a channel first.", "warning")
                return
            
            self.execute_bot_command(command)
                
        elif cmd == "history":
            if self.command_history:
                history_text = "\n".join([f"{i+1:2d}: {cmd}" 
                                        for i, cmd in enumerate(self.command_history[-10:])])
                self.print_to_console(f"Recent command history:\n{history_text}")
            else:
                self.print_to_console("No command history available")
                
        elif cmd == "exit":
            self.disconnect_bot()
            
        else:
            # Check if it might be a bot command without prefix
            if bot and bot.get_command(cmd):
                if not self.navigator.current_channel:
                    self.print_to_console("No channel selected. Use 'cd' to navigate to a channel first.", "warning")
                    return
                # Add prefix and execute
                self.execute_bot_command(f"{bot.command_prefix}{command}")
            else:
                self.print_to_console(f"Unknown command: {cmd}. Type 'help' for available commands.", "warning")
            
        # Update command count
        current_count = int(self.stats["commands"]["text"]) if self.stats["commands"]["text"].isdigit() else 0
        self.stats["commands"].config(text=str(current_count + 1))
        
    def execute_bot_command(self, command):
        """Execute a bot command in the current channel"""
        if not bot or not bot.is_ready():
            self.print_to_console("Bot is not connected.", "error")
            return
            
        if not self.navigator.current_channel:
            self.print_to_console("No channel selected. Use 'cd' to navigate to a channel.", "warning")
            return
        
        async def run_command():
            try:
                # Create a mock message object for command processing
                class MockMessage:
                    def __init__(self, content, channel, author):
                        self.content = content
                        self.channel = channel
                        self.author = author
                        self.guild = channel.guild
                        self.id = 0
                        self.attachments = []
                        self.embeds = []
                        self.mention_everyone = False
                        self.mentions = []
                        self.channel_mentions = []
                        self.role_mentions = []
                        self.reactions = []
                        self.pinned = False
                        self.type = discord.MessageType.default
                        self.flags = discord.MessageFlags()
                        
                    async def delete(self):
                        # Mock delete method - does nothing since this is a fake message
                        pass
                        
                    async def edit(self, **kwargs):
                        pass
                        
                    async def add_reaction(self, emoji):
                        pass
                        
                    async def remove_reaction(self, emoji, member):
                        pass
                        
                    async def pin(self):
                        pass
                        
                    async def unpin(self):
                        pass
                
                # Create mock message
                mock_message = MockMessage(
                    content=command,
                    channel=self.navigator.current_channel,
                    author=bot.user  # Use bot as author for permissions
                )
                
                # Get command context
                ctx = await bot.get_context(mock_message)
                
                if ctx.command is None:
                    self.print_to_console(f"Command not found: {command}", "warning")
                    return
                
                self.print_to_console(f"🔧 Executing: {command} in #{self.navigator.current_channel.name}", "info")
                
                # Execute the command
                await bot.invoke(ctx)
                
                self.print_to_console(f"✅ Command executed successfully", "success")
                
            except discord.Forbidden:
                self.print_to_console("❌ Bot doesn't have permission to execute this command", "error")
            except discord.HTTPException as e:
                self.print_to_console(f"❌ HTTP error: {e}", "error")
            except Exception as e:
                self.print_to_console(f"❌ Command execution failed: {e}", "error")
                
        # Run the command in the bot's event loop
        if hasattr(bot, 'loop') and bot.loop and bot.loop.is_running():
            asyncio.run_coroutine_threadsafe(run_command(), bot.loop)
        else:
            self.print_to_console("Bot event loop not available", "error")
            
    def send_message_to_channel(self, message):
        """Send a message to the current channel"""
        if not self.navigator.current_channel:
            self.print_to_console("No channel selected. Use 'cd' to navigate to a channel.", "warning")
            return
            
        if not bot or not bot.is_ready():
            self.print_to_console("Bot is not connected.", "error")
            return
            
        async def send_msg():
            try:
                await self.navigator.current_channel.send(message)
                self.print_to_console(f"✅ Message sent to #{self.navigator.current_channel.name}", "success")
            except Exception as e:
                self.print_to_console(f"❌ Failed to send message: {e}", "error")
                
        if hasattr(bot, 'loop') and bot.loop and bot.loop.is_running():
            asyncio.run_coroutine_threadsafe(send_msg(), bot.loop)
        else:
            self.print_to_console("Bot event loop not available", "error")
            
    def history_up(self, event):
        """Navigate command history up"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
            
    def history_down(self, event):
        """Navigate command history down"""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        elif self.history_index >= len(self.command_history) - 1:
            self.command_entry.delete(0, tk.END)
            self.history_index = len(self.command_history)
            
    def autocomplete(self, event):
        """Basic autocomplete for commands"""
        current = self.command_entry.get()
        commands = ["ls", "cd", "pwd", "clear", "status", "servers", "channels", "send", "history", "help", "exit"]
        
        matches = [cmd for cmd in commands if cmd.startswith(current.lower())]
        if len(matches) == 1:
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, matches[0] + " ")
            
        return "break"  # Prevent default tab behavior
        
    def update_path_display(self):
        """Update the path display in the header"""
        self.path_label.config(text=self.navigator.get_current_path())
        
    def print_to_console(self, message, tag=None):
        """Print message to console with optional formatting tag"""
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        
        self.console.config(state='normal')
        
        if tag == "prompt":
            self.console.insert(tk.END, f"{message}\n", tag)
        else:
            full_message = f"{timestamp}{message}\n"
            self.console.insert(tk.END, full_message, tag)
            
        self.console.config(state='disabled')
        self.console.see(tk.END)
        
    def check_queue(self):
        """Check message queue for bot updates"""
        try:
            while not message_queue.empty():
                message = message_queue.get_nowait()
                
                if isinstance(message, dict):
                    # Handle structured messages from bot
                    if message.get("type") == "status_update":
                        self.update_bot_status(message.get("online", False))
                    elif message.get("type") == "stats_update":
                        self.update_statistics(message.get("data", {}))
                else:
                    # Handle plain text messages
                    self.print_to_console(str(message))
                    
                    # Auto-detect status changes
                    msg_str = str(message).lower()
                    if "logged in" in msg_str or "connected" in msg_str:
                        self.update_bot_status(True)
                    elif "disconnected" in msg_str or "logged out" in msg_str:
                        self.update_bot_status(False)
                        
        except Exception as e:
            self.print_to_console(f"Queue processing error: {e}", "error")
            
        # Schedule next check
        self.root.after(100, self.check_queue)
        
    def update_bot_status(self, online):
        """Update bot status indicator"""
        if online:
            self.status_dot.itemconfig(self.status_circle, fill=self.colors['success'])
            self.status_label.config(text="Online", fg=self.colors['success'])
            self.refresh_status()
        else:
            self.status_dot.itemconfig(self.status_circle, fill=self.colors['error'])
            self.status_label.config(text="Offline", fg=self.colors['error'])
            
    def update_statistics(self, stats_data):
        """Update statistics display"""
        for key, value in stats_data.items():
            if key in self.stats:
                self.stats[key].config(text=str(value))
                
    def refresh_status(self):
        """Refresh bot status and statistics"""
        global bot
        
        if not bot:
            self.print_to_console("Bot instance not available", "warning")
            return
            
        try:
            if bot.is_ready():
                # Update statistics
                guild_count = len(bot.guilds)
                channel_count = sum(len(guild.channels) for guild in bot.guilds)
                user_count = sum(guild.member_count or 0 for guild in bot.guilds)
                
                self.stats["servers"].config(text=str(guild_count))
                self.stats["channels"].config(text=str(channel_count))
                self.stats["users"].config(text=str(user_count))
                
                # Update server list
                self.update_server_display()
                
                self.print_to_console(f"Status updated: {guild_count} servers, {user_count} users", "success")
            else:
                self.print_to_console("Bot is not ready", "warning")
                
        except Exception as e:
            self.print_to_console(f"Error refreshing status: {e}", "error")
            
    def update_server_display(self):
        """Update the server list display"""
        global bot
        
        # Clear existing server widgets
        for widget in self.servers_frame.winfo_children():
            widget.destroy()
            
        if not bot or not bot.guilds:
            tk.Label(
                self.servers_frame, text="No servers",
                fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'],
                font=('JetBrains Mono', 9)
            ).pack()
            return
            
        for guild in bot.guilds[:8]:  # Limit display to prevent overflow
            server_frame = tk.Frame(self.servers_frame, bg=self.colors['bg_secondary'])
            server_frame.pack(fill="x", pady=2)
            
            # Server icon (if available)
            if guild.icon:
                try:
                    icon_img = load_image_from_url(guild.icon.url, size=(24, 24))
                    if icon_img:
                        icon_label = tk.Label(server_frame, image=icon_img, bg=self.colors['bg_secondary'])
                        icon_label.image = icon_img  # Keep reference
                        icon_label.pack(side="left", padx=(0, 8))
                except:
                    pass
                    
            # Server name
            name_label = tk.Label(
                server_frame, text=guild.name[:20] + ("..." if len(guild.name) > 20 else ""),
                fg=self.colors['text_primary'], bg=self.colors['bg_secondary'],
                font=('JetBrains Mono', 9)
            )
            name_label.pack(side="left")
            
            # Member count
            member_label = tk.Label(
                server_frame, text=f"({guild.member_count or 0})",
                fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'],
                font=('JetBrains Mono', 8)
            )
            member_label.pack(side="right")
            
    def clear_console(self):
        """Clear the console output"""
        self.console.config(state='normal')
        self.console.delete(1.0, tk.END)
        self.console.config(state='disabled')
        self.print_to_console("Console cleared", "info")
        
    def show_detailed_stats(self):
        """Show detailed bot statistics"""
        global bot
        
        if not bot or not bot.is_ready():
            self.print_to_console("Bot not ready for detailed stats", "warning")
            return
            
        try:
            stats = []
            stats.append("=== DETAILED BOT STATISTICS ===")
            stats.append(f"Bot User: {bot.user.name}#{bot.user.discriminator}")
            stats.append(f"Bot ID: {bot.user.id}")
            stats.append(f"Servers: {len(bot.guilds)}")
            
            total_channels = sum(len(guild.channels) for guild in bot.guilds)
            text_channels = sum(len(guild.text_channels) for guild in bot.guilds)
            voice_channels = sum(len(guild.voice_channels) for guild in bot.guilds)
            
            stats.append(f"Total Channels: {total_channels}")
            stats.append(f"  • Text: {text_channels}")
            stats.append(f"  • Voice: {voice_channels}")
            
            total_members = sum(guild.member_count or 0 for guild in bot.guilds)
            stats.append(f"Total Members: {total_members}")
            
            # Largest servers
            largest_servers = sorted(bot.guilds, key=lambda g: g.member_count or 0, reverse=True)[:3]
            stats.append("Largest Servers:")
            for guild in largest_servers:
                stats.append(f"  • {guild.name}: {guild.member_count or 0} members")
                
            self.print_to_console("\n".join(stats), "info")
            
        except Exception as e:
            self.print_to_console(f"Error generating detailed stats: {e}", "error")
            
    def disconnect_bot(self):
        """Disconnect the bot"""
        if messagebox.askokcancel("Disconnect Bot", 
                                 "Are you sure you want to disconnect the bot?",
                                 icon=messagebox.WARNING):
            self.print_to_console("Disconnecting bot...", "warning")
            
            # Update status immediately
            self.update_bot_status(False)
            
            # Try to close bot gracefully
            if bot and hasattr(bot, 'close'):
                if hasattr(bot, 'loop') and bot.loop and bot.loop.is_running():
                    asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
                    
            self.print_to_console("Bot disconnected", "error")
            
    def lighten_color(self, hex_color):
        """Lighten a hex color for hover effects"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Lighten by adding 20 to each component (max 255)
        lightened = tuple(min(255, c + 20) for c in rgb)
        
        # Convert back to hex
        return f"#{lightened[0]:02x}{lightened[1]:02x}{lightened[2]:02x}"


def run_bot():
    """Run the Discord bot in its own thread"""
    global bot
    
    bot_token = os.getenv('DISCORD_TOKEN')
    if not bot_token:
        message_queue.put("Error: No Discord token found in .env file!")
        return
        
    # Create bot instance
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    intents.guild_messages = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        message_queue.put(f"Bot logged in as {bot.user.name}")
        message_queue.put(f"Connected to {len(bot.guilds)} servers")
        
        # Send structured status update
        message_queue.put({
            "type": "status_update",
            "online": True
        })
        
        # Send statistics update
        stats = {
            "servers": len(bot.guilds),
            "channels": sum(len(guild.channels) for guild in bot.guilds),
            "users": sum(guild.member_count or 0 for guild in bot.guilds),
            "commands": 0
        }
        message_queue.put({
            "type": "stats_update",
            "data": stats
        })
    
    @bot.event
    async def on_guild_join(guild):
        message_queue.put(f"Joined server: {guild.name} ({guild.member_count} members)")
        
    @bot.event
    async def on_guild_remove(guild):
        message_queue.put(f"Left server: {guild.name}")
        
    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
            
        # Log commands being used
        if message.content.startswith(bot.command_prefix):
            message_queue.put(f"Command used by {message.author.name} in #{message.channel.name}: {message.content}")
            
        await bot.process_commands(message)
    
    @bot.event
    async def on_disconnect():
        message_queue.put("Bot disconnected from Discord")
        message_queue.put({
            "type": "status_update", 
            "online": False
        })
    
    @bot.event
    async def on_resumed():
        message_queue.put("Bot reconnected to Discord")
        message_queue.put({
            "type": "status_update",
            "online": True
        })
    
    # Add some basic commands for testing
    @bot.command(name='ping')
    async def ping_command(ctx):
        """Test command to check bot responsiveness"""
        latency = round(bot.latency * 1000)
        await ctx.send(f'Pong! Latency: {latency}ms')
        message_queue.put(f"Ping command executed: {latency}ms latency")
    
    @bot.command(name='info')
    async def info_command(ctx):
        """Show bot information"""
        embed = discord.Embed(
            title="Osmium Bot", 
            description="Discord Bot Dashboard",
            color=0x58a6ff
        )
        embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
        embed.add_field(name="Users", value=sum(g.member_count or 0 for g in bot.guilds), inline=True)
        embed.add_field(name="Channels", value=sum(len(g.channels) for g in bot.guilds), inline=True)
        
        await ctx.send(embed=embed)
        message_queue.put(f"Info command executed in {ctx.guild.name}")
    
    # Start the bot
    message_queue.put("Starting Discord bot...")
    
    try:
        bot.run(bot_token)
    except discord.LoginFailure:
        message_queue.put("Invalid Discord token!")
    except Exception as e:
        message_queue.put(f"Bot error: {e}")
    finally:
        message_queue.put("Bot has shut down")


def start_gui():
    """Initialize and run the GUI"""
    root = tk.Tk()
    
    # Set window icon if available
    try:
        root.iconbitmap('icon.ico')  # Add your icon file
    except:
        pass
        
    dashboard = BotDashboard(root)
    
    # Redirect stdout and stderr to message queue
    sys.stdout = ConsoleRedirector(message_queue)
    sys.stderr = ConsoleRedirector(message_queue)
    
    # Start the bot in a separate daemon thread
    bot_thread = threading.Thread(target=lambda: run_bot_with_dashboard(bot) if bot else run_bot(), daemon=True)
    bot_thread.start()
    
    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit the dashboard?"):
            # Try to close bot gracefully
            if bot and hasattr(bot, 'close'):
                try:
                    if hasattr(bot, 'loop') and bot.loop and bot.loop.is_running():
                        asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
                except:
                    pass
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI main loop
    try:
        root.mainloop()
    except Exception as e:
        print(f"GUI error: {e}")
    finally:
        # Restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


def run_bot_standalone():
    """Fallback function if no bot instance is provided"""
    message_queue.put("No bot instance provided. Please use run_bot_with_dashboard(your_bot) or set the bot instance.")
    message_queue.put("Example usage:")
    message_queue.put("from dashboard import set_bot_instance, start_gui")
    message_queue.put("set_bot_instance(your_bot)")
    message_queue.put("start_gui()")


def run_bot_with_dashboard(bot_instance):
    """Run an existing bot instance with dashboard integration"""
    if bot_instance:
        set_bot_instance(bot_instance)
        
        # Get the bot token from environment or bot instance
        bot_token = os.getenv('DISCORD_TOKEN')
        if not bot_token:
            message_queue.put("Error: No Discord token found in .env file!")
            return
            
        message_queue.put("Starting integrated bot...")
        
        try:
            bot_instance.run(bot_token)
        except discord.LoginFailure:
            message_queue.put("Invalid Discord token!")
        except Exception as e:
            message_queue.put(f"Bot error: {e}")
        finally:
            message_queue.put("Bot has shut down")
    else:
        run_bot()


# Alternative initialization function for external bot integration
def start_gui_with_bot(bot_instance, bot_token=None):
    """Start GUI with an existing bot instance and run the bot"""
    global bot
    bot = bot_instance
    set_bot_instance(bot_instance)
    
    # Set token if provided
    if bot_token:
        os.environ['DISCORD_TOKEN'] = bot_token
    
    root = tk.Tk()
    dashboard = BotDashboard(root)
    
    # Redirect stdout and stderr to message queue
    sys.stdout = ConsoleRedirector(message_queue)
    sys.stderr = ConsoleRedirector(message_queue)
    
    # Start the bot in a separate daemon thread
    bot_thread = threading.Thread(target=lambda: run_bot_with_dashboard(bot_instance), daemon=True)
    bot_thread.start()
    
    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit the dashboard?"):
            # Try to close bot gracefully
            if bot and hasattr(bot, 'close'):
                try:
                    if hasattr(bot, 'loop') and bot.loop and bot.loop.is_running():
                        asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
                except:
                    pass
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI main loop
    try:
        root.mainloop()
    except Exception as e:
        print(f"GUI error: {e}")
    finally:
        # Restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


def run_bot_async_with_dashboard(bot_instance, bot_token=None):
    """Alternative method for running bot with async integration"""
    global bot
    bot = bot_instance
    set_bot_instance(bot_instance)
    
    if bot_token:
        os.environ['DISCORD_TOKEN'] = bot_token
    
    async def start_bot():
        token = bot_token or os.getenv('DISCORD_TOKEN')
        if not token:
            message_queue.put("Error: No Discord token provided!")
            return
            
        try:
            message_queue.put("Starting integrated bot (async)...")
            await bot_instance.start(token)
        except discord.LoginFailure:
            message_queue.put("Invalid Discord token!")
        except Exception as e:
            message_queue.put(f"Bot error: {e}")
    
    # Start bot in background thread
    def run_bot_thread():
        try:
            asyncio.run(start_bot())
        except Exception as e:
            message_queue.put(f"Bot thread error: {e}")
    
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    return bot_thread


# Usage example
if __name__ == "__main__":
    # Make sure you have a .env file with DISCORD_TOKEN=your_bot_token_here
    # or set the environment variable
    
    # Example of setting up environment variable programmatically:
    # os.environ['DISCORD_TOKEN'] = 'your_bot_token_here'
    
    start_gui()