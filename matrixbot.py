### MATRIX BOT
import asyncio
import csv
import datetime
import json
import os
import time

import cv2
import discord
import imgkit
import numpy as np
import pandas as pd
import requests
from discord import app_commands
from discord.ui import Button, View
from PIL import Image, ImageOps
from pyppeteer import launch

"""
 * API Specifications
 *
 * :subreddit = subreddit name
 * :modname = moderator name
 * :timeFromNow = time from now in seconds
 * :timeframeFrom = timeframe start in UTC Timestamp
 * :timeframeTo = timeframe endpoint in UTC Timestamp
 *
 * --- Subreddit Details ---
 *
 * /log/:subreddit/all
 * /log/:subreddit/time/last/:timeFromNow
 * /log/:subreddit/time/from/:timeframeFrom/to/:timeframeTo
 *
 * --- Moderator Details ---
 *
 * /log/:subreddit/mod/:modname
 * /log/:subreddit/mod/:modname/time/last/:timeFromNow
 * /log/:subreddit/mod/:modname/time/from/:timeframeFrom/to/:timeframeTo
"""


try:
    os.mkdir("temp")
except:
    pass


async def api_data(query="", onlymods=False, concise=False):
    global start, data
    url_matrix = f"https://lukebot.rcloud3.xyz/log/{query}"
    headers = {
        "CF-Access-Client-Id": data["CF-Access-Client-Id"],
        "CF-Access-Client-Secret": data["CF-Access-Client-Secret"],
    }
    response = await asyncio.get_event_loop().run_in_executor(
        None, lambda: requests.get(url_matrix, headers=headers)
    )
    print("API Call:", response.elapsed.total_seconds())
    recs = response.json()

    if recs:
        mod_actions = []
        mod_to_actions = {}
        for rec in recs:
            t = [(i["action"], i["count"]) for i in rec["actions"]]
            d = dict(t)
            d.update({"total": rec["count"]})
            mod_to_actions[rec["_id"]] = d
            for i in d.keys():
                if i not in mod_actions:
                    mod_actions.append(i)
        mod_actions.append("total")
        table = []
        for i, j in mod_to_actions.items():
            row = [i]
            for k in mod_actions:
                row.append(j.get(k, 0))
            table.append(row)
        table.insert(0, ["mod", *mod_actions])

        with open("temp/output.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerows(table)

        df = await asyncio.get_event_loop().run_in_executor(
            None, lambda: pd.read_csv("temp/output.csv")
        )

        df = df.drop(df.columns[-1], axis=1)

        cols = list(df.columns)
        cols.remove("total")
        cols.append("total")
        df = df[cols]
        total_actions = df["total"].sum()
        df["% actions"] = round((df["total"] / total_actions) * 100, 0).astype(int)
        df = df.sort_values(by=["total"], ascending=False)
        df.to_csv("temp/output.csv", index=False)
        new_df = ""
        if onlymods:
            new_df = pd.DataFrame(df["mod"])
            new_df.to_csv("temp/output.csv", index=False)
        elif concise:
            cols = df.columns.tolist()

            # Move the last two columns to the 2nd and 3rd positions
            cols.insert(1, cols.pop(-2))
            cols.insert(2, cols.pop())

            # Reorder the columns in the DataFrame
            df = df[cols]
            df = df.drop(df.columns[3:], axis=1)
            df.to_csv("temp/output.csv", index=False)
        else:
            df.to_csv("temp/output.csv", index=False)

        pd.read_csv("temp/output.csv").to_html("temp/Table.html")

        with open("temp/Table.html", "a") as f:
            f.write(open("format.html").read())

        if os.name == "nt":

            async def image_process():
                browser = await launch()
                page = await browser.newPage()
                await page.goto("file:///" + os.path.abspath("temp/Table.html"))
                await page.screenshot({"path": "temp/ss.png", "fullPage": "true"})
                await browser.close()

            await image_process()
        else:
            imgkit.from_file("temp/Table.html", "temp/ss.png")

        img = cv2.imread("temp/ss.png")
        blurred = cv2.blur(img, (3, 3))
        canny = cv2.Canny(blurred, 50, 200)
        pts = np.argwhere(canny > 0)
        y1, x1 = pts.min(axis=0)
        y2, x2 = pts.max(axis=0)
        cropped = img[y1:y2, x1:x2]
        cv2.imwrite("temp/cropped.png", cropped)
        ImageOps.expand(Image.open("temp/cropped.png"), border=10, fill="white").save(
            "temp/output.png"
        )

        print("Image Processing:", time.time() - start)
        start = time.time()
        return discord.File(open("temp/output.png", "rb"), filename="output.png")

    else:
        return -1

    # --- DISCORD ----


def webhook(content=None):
    global data
    url = data["webhook"]
    content = {"username": "Matrix Bot", "content": content}
    requests.post(url, json=content)


def dates(date):
    try:
        date_object = datetime.datetime.strptime(date, "%d/%m/%Y")
        start_time = date_object.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = date_object.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        start_timestamp = start_time.timestamp()
        end_timestamp = end_time.timestamp()

        return start_timestamp, end_timestamp
    except:
        return -1, -1


# ILLEGAL: "gaming", "explainlikeimfive"
f = open("sublist.txt", "r")
sublist = f.read().splitlines()
f.close()

f = open("data.json", "r")
data = json.load(f)
f.close()


class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=data["test_guild_id"]))
            self.synced = True
        print(f"Logged in as {self.user.name}")


client = aclient()
tree = app_commands.CommandTree(client, fallback_to_global=True)


async def send_message(
    interaction: discord.Interaction, text="", image=None, query="", only_webhook=False
):
    global start, data
    if image == -1:
        text = "```QUERY RETURNED NO RESULT```"
        image = None

    if not only_webhook:
        if image:
            embed = discord.Embed(
                title=query,
                color=0x2F4F4F,
            )
            embed.set_image(url="attachment://output.png")
            await interaction.followup.send(content=text, embeds=[embed], files=[image])
            text = query
        else:
            await interaction.followup.send(content=text)

    if interaction.guild is None:
        webhook(
            content=f"```{text}```\n```User: {interaction.user.name}```\n```Url: {interaction.channel.jump_url}/{interaction.id}```\n<@885418802815307817>"
        )
    else:
        webhook(
            content=f"```{text}```\n```User: {interaction.user.name}```\n```Channel: {interaction.channel.name}```\n```Server: {interaction.guild.name}```\n```Url: {interaction.channel.jump_url}/{interaction.id}```\n<@885418802815307817>"
        )

    print("Sending Message:", time.time() - start)
    start = time.time()


@tree.command(
    name="invite",
    description="Invite the bot to your server",
    guild=discord.Object(id=data["test_guild_id"]),
)
async def invite(interaction: discord.Interaction):
    global start, data
    start = time.time()
    await interaction.response.defer(thinking=True)
    invite_link = data["invite_link"]
    await send_message(
        interaction,
        text=f"Invite me to your server using this link:\n{invite_link}",
    )


@tree.command(
    name="help",
    description="Help",
    guild=discord.Object(id=data["test_guild_id"]),
)
async def help(interaction: discord.Interaction):
    global start, data
    start = time.time()
    await interaction.response.defer(thinking=True)
    help_text = """```yaml
1) Help:
/help

2) List of available subreddits:
/sublist

3) Subreddit Mod logs Matrix:
/matrix <subreddit> [filter1, filter2, ...]

4) Filters:
    a) moderator (moderator name)
    b) date (dd/mm/yyyy)
       days (number of days)
       seconds (number of seconds)
    c) onlymods
    d) concise

5) Example:
    a) /matrix cats mod=Xyreo date=14/03/2023 concise

       - Returns Mod logs of r/cats by u/Xyreo on 14 March, 2023, with only the total mod actions.

    b) /matrix cats days=7 onlymods

       - Returns Mod logs of r/cats by all mods in the last 7 days, with only the name of the mods.

    c) /matrix cats mod=Xyreo seconds=3600

       - Returns Mod logs of r/cats by u/Xyreo in the last hour, with all the details.

Credit to Xyreo, ZockerMarcelo and okaybro for developing this feature <3```
"""
    await send_message(interaction, text=help_text)


@tree.command(
    name="sublist",
    description="List of subreddits available",
    guild=discord.Object(id=data["test_guild_id"]),
)
async def sublist_command(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    global start, data
    start = time.time()
    split_len = 15
    pages = {}
    for i in range(0, len(sublist), split_len):
        d = {}
        for j in range(i, min(i + split_len, len(sublist))):
            d[j + 1] = "r/" + sublist[j]
        pages[i // split_len + 1] = d

    next = Button(style=discord.ButtonStyle.green, label="Next")
    prev = Button(style=discord.ButtonStyle.green, label="Prev", disabled=True)
    view = View(timeout=None)
    view.add_item(prev)
    view.add_item(next)

    def pprint(d):
        s = ""
        for i in d:
            s += f"{i}. {d[i]}\n"
        return s

    async def page_change(interaction: discord.Interaction, change):
        page_number = int(
            interaction.message.embeds[0].footer.text.split("/")[0].split(" ")[1]
        )
        page_number += change
        if page_number == len(pages):
            next.disabled = True
        if page_number == 1:
            prev.disabled = True
        if page_number < len(pages) and page_number > 1:
            next.disabled = False
            prev.disabled = False
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Available Subreddits",
                description=pprint(pages[page_number]),
            ).set_footer(text=f"Page {page_number}/{len(pages)}"),
            view=view,
        )

    next.callback = lambda i: page_change(i, 1)
    prev.callback = lambda i: page_change(i, -1)
    await interaction.followup.send(
        embed=discord.Embed(
            title="Available Subreddits",
            description=pprint(pages[1]),
        ).set_footer(text=f"Page 1/{len(pages)}"),
        view=view,
    )

    await send_message(interaction, text="Available Subreddits", only_webhook=True)


@tree.command(
    name="matrix",
    description="Mod logs Matrix",
    guild=discord.Object(id=data["test_guild_id"]),
)
@app_commands.describe(
    subreddit="Subreddit Name",
    mod="Filters by Moderator Name",
    onlymods="Only names of moderators are displayed",
    concise="Only total mod actions are displayed",
    date="Specific Date's Mod logs",
    days="Last n days' Mod logs",
    seconds="Last n seconds' Mod logs",
)
async def matrix_command(
    interaction: discord.Interaction,
    subreddit: str,
    mod: str = None,
    onlymods: bool = False,
    concise: bool = False,
    date: str = None,
    days: int = None,
    seconds: int = None,
):
    global start, data
    start = time.time()
    await interaction.response.defer(thinking=True)
    if days and seconds:
        await send_message(
            interaction=interaction,
            text="```ERROR! 'DAYS' CANNOT BE USED WITH 'SECONDS'```",
        )
        return
    if date and (days or seconds):
        await send_message(
            interaction=interaction,
            text="```ERROR! 'DATE' CANNOT BE USED WITH 'DAYS' OR 'SECONDS'```",
        )
        return

    if subreddit in sublist:
        query = f"{subreddit}"
        if mod:
            query += f"/mod/{mod}"
        if date:
            start_timestamp, end_timestamp = dates(date)
            if start_timestamp == end_timestamp == -1:
                await send_message(
                    interaction=interaction,
                    text=f"```ERROR! INVALID 'DATE' FORMAT, USE 'DD/MM/YYYY'```",
                )
                return
            query += f"/time/from/{start_timestamp}/to/{end_timestamp}"
        elif days:
            query += f"/time/last/{int(days)*86400}"
        elif seconds:
            query += f"/time/last/{seconds}"

        if "/" not in query:
            query += "/all"

        print("Query Processing:", time.time() - start)
        start = time.time()
        image = await api_data(query, onlymods, concise)
        query = f"Mod logs of r/{subreddit}"
        if mod:
            query += f" by u/{mod}"
        if date:
            if os.name == "nt":
                date_str = datetime.datetime.strptime(date, "%d/%m/%Y").strftime(
                    "%#d %b, %Y"
                )
            else:
                date_str = datetime.datetime.strptime(date, "%d/%m/%Y").strftime(
                    "%-d %b, %Y"
                )
            query += f" on {date_str}"
        elif days:
            query += f" in the last {days} days"
        elif seconds:
            query += f" in the last {seconds} seconds"
        await send_message(
            interaction=interaction,
            image=image,
            query=query,
        )
        return
    else:
        await send_message(
            interaction=interaction,
            text=f"```ERROR! SUBREDDIT '{subreddit}' NOT IN DATABASE```",
        )
        return


client.run(data["token"])
