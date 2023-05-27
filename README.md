# Matrix-Bot

## A Bot for Reddit Mod's Action Logs

This bot is designed to take the action logs from a subreddit and post it to a discord channel, in a well formatted table, using slash commands.

### Setup

`data.json` contains the data needed to run the bot. It is formatted as a JSON object, with the following keys:

```
"webhook" - The webhook URL for the discord channel
"token" - The bot token
"invite_link" - The link to invite the bot to a server
"CF-Access-Client-Id" - The Cloudflare Access Client ID
"CF-Access-Client-Secret" - The Cloudflare Access Client Secret
"owner_ids" - List of user IDs that have admin permissions
"google-cred" - Google cloud credentials
```

`sublist.txt` contains the list of subreddits that the bot has access to. Each subreddit should be on a new line.

### Running

To run the bot, simply run `python3 matrixbot.py` in the root directory of the project. The bot will then start up and begin listening for events.
