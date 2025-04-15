message_queue = Queue()

class ConsoleRedirector:
    """Redirects stdout/stderr to the GUI console"""
    def __init__(self, queue):
        self.queue = queue

    def write(self, message):
        if message.strip():
            self.queue.put(message)

    def flush(self):
        pass

class BotConsole:
    def __init__(self, root):
        self.root = root
        self.root.title("Osmium Bot Dashboard")
        self.root.geometry("1000x600")
        self.command_history = []
        
        
        
        # Set dark theme colors
        self.bg_dark = "#2D2D2D"
        self.bg_darker = "#222222"
        self.text_color = "#E0E0E0"
        self.accent_color = "#2a3ffa"  # Using the COLOR value from the original code
        self.secondary_accent = "#3D5AFD"
        
        # Configure root appearance
        self.root.configure(bg=self.bg_dark)
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=7)
        self.root.rowconfigure(0, weight=1)
        
        # Create sidebar frame
        sidebar_frame = tk.Frame(root, bg=self.bg_darker, bd=0)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.columnconfigure(0, weight=1)
        
        # Create header in sidebar
        header_frame = tk.Frame(sidebar_frame, bg=self.accent_color, height=60)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_label = tk.Label(header_frame, text="OSMIUM", fg="white", bg=self.accent_color,
                               font=("Arial", 18, "bold"), pady=10)
        header_label.pack(fill="x")
        
        # Create status section
        status_frame = tk.Frame(sidebar_frame, bg=self.bg_darker, padx=10, pady=10)
        status_frame.grid(row=1, column=0, sticky="ew")
        
        status_label = tk.Label(status_frame, text="BOT STATUS", fg=self.accent_color, bg=self.bg_darker,
                               font=("Arial", 12, "bold"))
        status_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.status_indicator = tk.Canvas(status_frame, width=15, height=15, bg=self.bg_darker, 
                                         highlightthickness=0)
        self.status_indicator.grid(row=1, column=0, sticky="w")
        self.status_indicator.create_oval(0, 0, 15, 15, fill="gray", outline="")
        
        self.status_text = tk.Label(status_frame, text="Connecting...", fg=self.text_color, 
                                   bg=self.bg_darker, font=("Arial", 10))
        self.status_text.grid(row=1, column=1, sticky="w", padx=5)
        
        # Create stats section
        stats_frame = tk.Frame(sidebar_frame, bg=self.bg_darker, padx=10, pady=10)
        stats_frame.grid(row=2, column=0, sticky="ew", pady=10)
        
        stats_label = tk.Label(stats_frame, text="STATISTICS", fg=self.accent_color, bg=self.bg_darker,
                              font=("Arial", 12, "bold"))
        stats_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        tk.Label(stats_frame, text="Servers:", fg=self.text_color, bg=self.bg_darker).grid(row=1, column=0, sticky="w")
        self.servers_count = tk.Label(stats_frame, text="--", fg=self.text_color, bg=self.bg_darker)
        self.servers_count.grid(row=1, column=1, sticky="e", padx=10)
        
        tk.Label(stats_frame, text="Users:", fg=self.text_color, bg=self.bg_darker).grid(row=2, column=0, sticky="w")
        self.users_count = tk.Label(stats_frame, text="--", fg=self.text_color, bg=self.bg_darker)
        self.users_count.grid(row=2, column=1, sticky="e", padx=10)
        
        tk.Label(stats_frame, text="Commands:", fg=self.text_color, bg=self.bg_darker).grid(row=3, column=0, sticky="w")
        self.commands_count = tk.Label(stats_frame, text="0", fg=self.text_color, bg=self.bg_darker)
        self.commands_count.grid(row=3, column=1, sticky="e", padx=10)
        
        self.icons_frame = tk.Frame(stats_frame, bg=self.bg_darker)
        self.icons_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        bottom_frame = tk.Frame(self, bg="#1e1e1e", height=40)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.entry = tk.Entry(bottom_frame, bg="#2e2e2e", fg="white", insertbackground="white", font=("Consolas", 12))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), pady=10)
        self.entry.bind("<Return>", self.process_command)

        send_button = tk.Button(bottom_frame, text="Send", bg="#3a3a3a", fg="white", command=self.process_command)
        send_button.pack(side=tk.RIGHT, padx=(5, 10), pady=10)

    def history_up(self, event):
        if self.command_history:
            self.history_index = max(0, self.history_index - 1)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.command_history[self.history_index])

    def history_down(self, event):
        if self.command_history:
            self.history_index = min(len(self.command_history) - 1, self.history_index + 1)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.command_history[self.history_index])
    
def update_server_icons(self):
    # Clear old icons
    for widget in self.icons_frame.winfo_children():
        widget.destroy()

    if not hasattr(bot, 'guilds'):
        return

    self.server_icons = []  # Store to prevent garbage collection

    for guild in bot.guilds[:5]:  # Limit to 5 for space
        if guild.icon:
            url = guild.icon.url
            icon_img = load_image_from_url(url)
            if icon_img:
                lbl = tk.Label(self.icons_frame, image=icon_img, bg=self.bg_darker)
                lbl.image = icon_img
                lbl.pack(side=tk.LEFT, padx=2)
                self.server_icons.append(icon_img)
        
        # Create action buttons
        actions_frame = tk.Frame(sidebar_frame, bg=self.bg_darker, padx=10, pady=10)
        actions_frame.grid(row=3, column=0, sticky="ew", pady=10)
        
        actions_label = tk.Label(actions_frame, text="ACTIONS", fg=self.accent_color, bg=self.bg_darker,
                                font=("Arial", 12, "bold"))
        actions_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Helper function for styled buttons
        def create_button(parent, text, command, row):
            btn = tk.Button(parent, text=text, command=command, 
                           bg=self.bg_dark, fg=self.text_color,
                           activebackground=self.secondary_accent, 
                           activeforeground="white",
                           relief=tk.FLAT, padx=10, pady=5,
                           width=15)
            btn.grid(row=row, column=0, sticky="ew", pady=3)
            return btn
        
        self.clear_btn = create_button(actions_frame, "Clear Console", self.clear_console, 1)
        self.status_btn = create_button(actions_frame, "Check Status", self.check_status, 2)
        self.exit_btn = create_button(actions_frame, "Exit Bot", self.exit_bot, 3)
        
        # Create main content frame
        main_frame = tk.Frame(root, bg=self.bg_dark, padx=10, pady=10)
        main_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=0)  # Header
        main_frame.rowconfigure(1, weight=1)  # Console
        main_frame.rowconfigure(2, weight=0)  # Input area
        
        # Main header
        main_header = tk.Label(main_frame, text="CONSOLE OUTPUT", fg=self.accent_color, bg=self.bg_dark,
                              font=("Arial", 14, "bold"), anchor="w")
        main_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Create log widget with styled appearance
        self.log = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD, 
            bg=self.bg_darker, 
            fg=self.text_color, 
            insertbackground=self.text_color,
            relief=tk.FLAT,
            font=("Consolas", 10),
            state='disabled'
        )
        self.log.grid(row=1, column=0, sticky="nsew")
        
        # Create input frame
        input_frame = tk.Frame(main_frame, bg=self.bg_dark, pady=10)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)
        
        # Create input widgets
        self.entry = tk.Entry(
            input_frame, 
            width=70,
            bg=self.bg_darker,
            fg=self.text_color,
            insertbackground=self.text_color,
            relief=tk.FLAT,
            font=("Consolas", 10)
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 10), ipady=5)
        self.entry.bind("<Return>", self.send_command)
        self.entry.bind("<Up>", self.history_up)
        self.entry.bind("<Down>", self.history_down)
        
        self.send_button = tk.Button(
            input_frame, 
            text="Send", 
            command=self.send_command,
            bg=self.accent_color,
            fg="white",
            activebackground=self.secondary_accent,
            activeforeground="white",
            relief=tk.FLAT,
            padx=15
        )
        self.send_button.grid(row=0, column=1, padx=5)
        
        # Setup command counter
        self.command_count = 0
        
        # Setup periodic queue checking
        self.check_queue()
        
        self.print("Bot console started. Connecting to Discord...")

    def set_status_online(self):
        """Update status indicator to show the bot is online"""
        self.status_indicator.itemconfig(1, fill="#4CAF50")  # Green
        self.status_text.config(text="Online")

    def set_status_offline(self):
        """Update status indicator to show the bot is offline"""
        self.status_indicator.itemconfig(1, fill="#F44336")  # Red
        self.status_text.config(text="Offline")

    def update_stats(self, guilds=None, members=None):
        """Update the statistics display"""
        if guilds is not None:
            self.servers_count.config(text=str(guilds))
            update_server_icons()
        if members is not None:
            self.users_count.config(text=str(members))
    
    def print_discord_command(self, author, content):
    # Log avatar + command
        self.print(f"{author['name']}: {content}")
        avatar_url = author.get("avatar_url")

        if avatar_url:
            img = load_image_from_url(avatar_url, size=(24, 24))
            if img:
                # Insert avatar image before text
                self.log.configure(state='normal')
                self.log.image_create(tk.END, image=img)
                self.log.insert(tk.END, f" {author['name']}: {content}\n")
                self.log.configure(state='disabled')
                self.log.see(tk.END)

                # Keep reference
                if not hasattr(self, 'avatars'):
                    self.avatars = []
                self.avatars.append(img)

    def check_queue(self):
        """Check for new messages in the queue and update the log"""
        try:
            while not message_queue.empty():
                message = message_queue.get_nowait()
                self.print(message)
                
                # Check for status updates in messages
                if "connected to Discord" in str(message).lower():
                    self.set_status_online()
                    
                # Try to extract guild count information
                if "connected to" in str(message).lower() and "servers" in str(message).lower():
                    try:
                        guilds = int(str(message).split("Connected to ")[1].split(" servers")[0])
                        self.update_stats(guilds=guilds)
                    except:
                        pass
                if isinstance(message, dict) and "content" in message and "author" in message:
                    self.print_discord_command(message["author"], message["content"])
                else:
                    self.print(message)
                
                if "bot has shut down" in str(message).lower():
                    self.set_status_offline()
                    
        except Exception as e:
            self.print(f"Queue error: {e}")
            
        # Schedule to run again after 100ms
        self.root.after(100, self.check_queue)

    def print(self, message):
        """Add text to the console log"""
        if not isinstance(message, str):
            message = str(message)
            
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        message_with_timestamp = timestamp + message
            
        self.log.configure(state='normal')
        self.log.insert(tk.END, f"{message_with_timestamp}\n")
        
        # Add colored text for certain keywords
        if "error" in message.lower():
            line_start = self.log.index("end-1c linestart")
            line_end = self.log.index("end-1c")
            self.log.tag_add("error", line_start, line_end)
            self.log.tag_config("error", foreground="#FF5252")
        elif "connected" in message.lower() or "success" in message.lower():
            line_start = self.log.index("end-1c linestart")
            line_end = self.log.index("end-1c")
            self.log.tag_add("success", line_start, line_end)
            self.log.tag_config("success", foreground="#4CAF50")
            
        self.log.configure(state='disabled')
        self.log.see(tk.END)  # Auto-scroll to the end

    def send_command(self, event=None):
        """Process commands entered in the console"""
        command = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        if not command:
            return
            
        self.print(f"> {command}")
        self.command_count += 1
        self.commands_count.config(text=str(self.command_count))
        
        # Handle console commands
        if command.lower() == "shutdown" or command.lower() == "exit":
            self.exit_bot()
        elif command.lower() == "clear":
            self.clear_console()
        elif command.lower().startswith("status"):
            self.check_status()
        else:
            self.print("Command not recognized in console.")

    def clear_console(self):
        """Clear the console log"""
        self.log.configure(state='normal')
        self.log.delete(1.0, tk.END)
        self.log.configure(state='disabled')
        self.print("Console cleared.")

    def check_status(self):
        """Check and display bot status"""
        if not hasattr(bot, 'is_ready') or not callable(bot.is_ready):
            self.print("Bot reference not available.")
            return
            
        is_ready = bot.is_ready()
        guild_count = len(bot.guilds) if is_ready else 0
        
        if is_ready:
            self.set_status_online()
            self.update_stats(guilds=guild_count)
            # Calculate approximate user count (this may overcount shared users)
            user_count = sum(g.member_count for g in bot.guilds)
            self.update_stats(members=user_count)
            
            self.print(f"Bot is connected to {guild_count} servers")
            self.print(f"Serving approximately {user_count} users")
        else:
            self.set_status_offline()
            self.print("Bot is currently disconnected.")

    def exit_bot(self):
        """Safely shut down the bot and close the application"""
        if messagebox.askokcancel("Exit", "Shut down the bot?", 
                                 icon=messagebox.WARNING):
            self.print("Shutting down...")
            self.set_status_offline()
            # Schedule the bot to close in the bot's event loop
            if hasattr(bot, 'loop') and bot.loop and bot.loop.is_running():
                try:
                    asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
                except Exception as e:
                    self.print(f"Error shutting down bot: {e}")
            self.root.after(1000, self.root.destroy)  # Give it a second to close

def run_bot():
    """Run the Discord bot in its own thread"""
    bot_token = os.getenv('DISCORD_TOKEN')
    if not bot_token:
        message_queue.put("Error: No Discord token found in .env file!")
        return
        
    # Add your bot commands and events here or import them

    # Print startup message
    message_queue.put("Starting Discord bot...")
    
    try:
        bot.run(bot_token)
    except Exception as e:
        message_queue.put(f"Bot error: {e}")
    finally:
        message_queue.put("Bot has shut down.")

def start_gui():
    """Initialize and run the GUI"""
    root = tk.Tk()
    console = BotConsole(root)
    
    # Redirect stdout and stderr to the console
    sys.stdout = ConsoleRedirector(message_queue)
    sys.stderr = ConsoleRedirector(message_queue)
    
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start the GUI main loop
    try:
        root.mainloop()
    except Exception as e:
        print(f"GUI error: {e}")
    finally:
        # Restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__