# Overview: Talina
A Discord bot written in Python, able to use Slash commands.

Main functions include:
- /f1
   - schedule - for showing upcoming races.
   - upcoming_reminders - List pending F1 reminders
   - clear_reminders - Wipes all pending reminders
- /fn (Poor man's Nitro)
- /quote
   - add keyword quote -> add a new quote (writes to CSV)
   - list              -> list available keywords
   - random            -> get a random quote from whole DB
   - info id           -> view quote metadata (author, date added)
- And some minor ones, you can view them in the code.

As the functions are Slash commands, the usage should be self-explanatory.

# Installation
1) Install the required packages in `requirements.txt`
2) Generate a bot token
3) Create a .env file in the same directory as main.py and enter the token in the file like so:`TOKEN=[your token here]`
   - Or, if you can't get that working, just place the token in main.py at the bottom, replacing `os.environ['TOKEN']`.
5) Run main.py
6) Commit die

# Issues
- Some emotes in commands (For example, the custom emotes in certain `/f1` responses) won't show properly because your new instance of the bot won't be in the same servers as my original instance. Replace them with generic emotes or ones of your own choosing.

- Not well commented but what do you expect.

- Some functions could be slightly buggy. If it's something major that completely makes the functions unusable, let me know.
