import discord
from discord.ext import commands, tasks
import random
import traceback
import io
import re
import aiohttp

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

COG_EXTENSIONS = [
    "cogs.moderation",
    "cogs.admin",
    "cogs.customroles",
    "cogs.fun",
    "cogs.profiles",
    "cogs.achievements",
]

cogs_loaded = False

from common import formatUsername, getDisplay, loadData, saveData, truncateMessage, joinandleavechannelid, messageloggingchannelid, etanid, membercountid, serverid, starboardchannel, bottrapchannelid, lastcachedmembercount, prescencecycles, env

# ---- quote command helpers ----

import quote as quotescript

MENTION_RE = re.compile(r"<@!?(\d+)>|<@&(\d+)>|<#(\d+)>")

if "fallbackfontpaths" in env:
    quotescript.FALLBACK_FONT_PATHS = env["fallbackfontpaths"]

def resolveMentions(text, message):
    def repl(m):
        if m.group(1):
            uid = int(m.group(1))
            user = discord.utils.get(message.mentions, id=uid) or (message.guild.get_member(uid) if message.guild else None)
            return f"@{getDisplay(user)}" if user else "@unknown-user"
        if m.group(2):
            rid = int(m.group(2))
            role = discord.utils.get(message.role_mentions, id=rid) or (message.guild.get_role(rid) if message.guild else None)
            return f"@{role.name}" if role else "@unknown-role"
        if m.group(3):
            cid = int(m.group(3))
            chan = discord.utils.get(message.channel_mentions, id=cid) or (message.guild.get_channel(cid) if message.guild else None)
            return f"#{chan.name}" if chan else "#unknown-channel"
    return MENTION_RE.sub(repl, text)

# ---- end quote command helpers ----

# bot tasks
@tasks.loop(minutes=1)
async def membercount():
    global lastcachedmembercount # weatherupdate includes this as well cuz discord.py doesn't allow multiple tasks THAT TOOK AGES TO FIND OUT LMAO
    guild = bot.get_guild(serverid) # putting this here cuz idk if discord.py allows one task. if it does im gonna crashout cuz that shit took AGES // hi etan it did
    membercountchannel = guild.get_channel(membercountid)
    realmembercount = guild.member_count - sum(1 for member in guild.members if member.bot)
    if lastcachedmembercount != realmembercount:
        lastcachedmembercount = realmembercount
        await membercountchannel.edit(name=f"Members: {realmembercount}")

    await bot.change_presence(activity=discord.Game(prescencecycles[random.randint(0, len(prescencecycles) - 1)]), status=discord.Status.online)

# bot events
@bot.event
async def on_message_delete(message):
    if message.author.bot == False:
        channel = bot.get_channel(messageloggingchannelid)
        embed = discord.Embed(title="Message Deleted", description=f"Message from {formatUsername(message.author)} in {message.channel.mention}", color=discord.Color.red())
        embed.add_field(name="Content", value=truncateMessage(message.content, 1024) if message.content else "No content", inline=False)
        embed.add_field(name="Attachments", value=f"{len(message.attachments)} attachment(s)" if message.attachments else "No attachments", inline=False)
        embed.add_field(name="Attachment URLs", value="\n".join([attachment.url for attachment in message.attachments]) if message.attachments else "No attachments", inline=False)
        embed.set_image(url=message.attachments[0].url if message.attachments else None)
        await channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot == False and before.content != after.content:
        channel = bot.get_channel(messageloggingchannelid)
        embed = discord.Embed(title="Message Edited", description=f"Message from {formatUsername(before.author)} in {before.channel.mention}", color=discord.Color.orange())
        embed.add_field(name="Before", value=truncateMessage(before.content, 1024) if before.content else "No content", inline=False)
        embed.add_field(name="After", value=truncateMessage(after.content, 1024) if after.content else "No content", inline=False)
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    global cogs_loaded
    print("Loading, please wait...")
    await bot.wait_until_ready()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    if not cogs_loaded:
        for extension in COG_EXTENSIONS:
            await bot.load_extension(extension)
        cogs_loaded = True
    await bot.tree.sync()
    if not membercount.is_running():
        membercount.start()
    print("Bot is ready!")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(joinandleavechannelid)
    await channel.send(f"[+] Welcome {member.mention} to the server!")

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(joinandleavechannelid)
    await channel.send(f"[-] {formatUsername(member)} has left the server.")

@bot.event
async def on_raw_reaction_add(payload): # starboard function
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    reaction = discord.utils.get(message.reactions, emoji="⭐")
    starboarddata = loadData("starboard")
    if starboarddata == "":
        print("Error loading starboard data.")
        return
    if message.id in starboarddata:
        return
    if message.channel.id == starboardchannel:
        return
    if reaction and reaction.count >= 3:
        channel = bot.get_channel(starboardchannel)
        embed = discord.Embed(title="Starred Message", description=f"Message from {formatUsername(message.author)} in {message.channel.mention}", color=discord.Color.gold(), timestamp=message.created_at)
        embed.add_field(name="Content", value=truncateMessage(message.content, 1024) if message.content else "No content", inline=False)
        embed.add_field(name="Attachments", value=f"{len(message.attachments)} attachment(s)" if message.attachments else "No attachments", inline=False)
        embed.add_field(name="Attachment URLs", value="\n".join([attachment.url for attachment in message.attachments]) if message.attachments else "No attachments", inline=False)
        embed.add_field(name="Jump Link", value=f"[Click here to jump to the message]({message.jump_url})", inline=False)
        embed.set_image(url=message.attachments[0].url if message.attachments else None)
        embed.set_footer(text=f"Starboard is a beta feature! Please report bugs to etangaming123.")
        starboarddata.append(message.id)
        saveData("starboard", starboarddata)
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot: # ignore bot actions
        return

    if message.channel.id == bottrapchannelid: # ban those who send messages in the oh so obvious trap
        lchannelreal = bot.get_channel(messageloggingchannelid)
        try:
            await message.author.ban(delete_message_days=1)
        except discord.Forbidden:
            await message.delete()
            await lchannelreal.send(f"{formatUsername(message.author)} fell for the trap but i couldn't ban them...")
            return
        await lchannelreal.send(f"suspected bot {formatUsername(message.author)} fell for the trap, banned!")
        return

    if message.content == "h>quote": # i have no idea how this works
        await message.channel.typing()
        if not message.reference or not message.reference.resolved:
            await message.channel.send("Please reply to a message to quote someone!", reference=message, mention_author=False)
            return
        original_message = message.reference.resolved
        if not hasattr(original_message.author, "display_avatar") or not original_message.author.display_avatar:
            await message.channel.send("The original author has no profile picture!", reference=message, mention_author=False) # sorry default pfp users
            return
        try:
            # Download avatar
            async with aiohttp.ClientSession() as session:
                async with session.get(original_message.author.display_avatar.url) as resp:
                    avatar_bytes = await resp.read()

            # Get user's role color, default to white
            role_color = (255, 255, 255)
            availablecolors = []
            for role in original_message.author.roles:
                if role.color.value != 0:
                    availablecolors.append(role.color.to_rgb())
            availablecolors.reverse() # reverse so higher roles take precedence
            if availablecolors:
                role_color = availablecolors[0]

            # Resolve @mentions / #channel-names to readable text before handing off to the renderer
            resolved_text = resolveMentions(original_message.content, original_message)

            png_bytes = await quotescript.renderQuoteImage(
                content_text=resolved_text,
                author_display_name=getDisplay(original_message.author),
                author_username=original_message.author.name,
                avatar_bytes=avatar_bytes,
                font_path=env["fontpath"],
                role_color=role_color,
            )

            await message.channel.send(file=discord.File(io.BytesIO(png_bytes), filename="quote.png"), reference=message, mention_author=False)
        except Exception as e: # FAH
            traceback.print_exc()
            await message.channel.send(f"Error creating quote image: {str(e)}", reference=message, mention_author=False)


bot.run(env["token"])
