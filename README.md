# Matrix-Bot

<<<<<<< HEAD
## A Bot for Reddit Mod's Action Logs

This bot is designed to take the action logs from a subreddit and post it to a discord channel, in a well formatted table, using slash commands.

### Setup

`data.json` is a json file that contains the data needed to run the bot. It is formatted as a JSON object, with the following keys:

```
"webhook" - The webhook URL for the discord channel
"test_guild_id" - The ID of the test guild (For global commands, set to "")
"token" - The bot token
"invite_link" - The link to invite the bot to a server
"CF-Access-Client-Id" - The Cloudflare Access Client ID
"CF-Access-Client-Secret" - The Cloudflare Access Client Secret
```

### Running

To run the bot, simply run `python3 matrixbot.py` in the root directory of the project. The bot will then start up and begin listening for events.
=======
Get an instant image summary of the mod logs of subreddits simply by using slash commands on discord
>>>>>>> 5a6fce2bbbc1b468a268c0fdfff2620ebedcfacb
