import discord
from discord.ext import commands
import os
import json
from threading import Thread
from flask import Flask
from keep_alive import keep_alive

fwords = []

with open("filters.txt", "r") as f:
    for word in f.read().splitlines():
        fwords.append(word)
print(fwords)

intents = discord.Intents.default()
intents.members = True
cmd_prefix = 'm!'
client = commands.Bot(intents=intents, command_prefix=cmd_prefix)


def readd_rejoin_member_warning_points(username):
    with open("left_warnpoints.txt", "r") as f:
        try:
            pl = json.loads(f.read())
        except:
            return  # nobody :skull:
    val = pl[username]
    add_member(username, val)


def add_left_member_warning_points(
    username
):  # we will save warning points of left members in case they rejoin
    with open("warnpoints.txt", "r") as f:
        p = json.loads(f.read())
    val = p[username]
    if val == 0:  # dont need to add users with no warning points
        return
    with open("left_warnpoints.txt", "r") as f:
        try:
            pl = json.loads(f.read())
        except json.decoder.JSONDecodeError:  # it means this file does not have content
            pl = dict()
    pl[username] = val
    with open("left_warnpoints.txt", "w") as f:
        f.write(json.dumps(pl))


def remove_member(username):
    with open("warnpoints.txt", "r") as f:
        p = json.loads(f.read())
    p.pop(username)
    with open("warnpoints.txt", "w") as f:
        f.write(json.dumps(p))


def get_val(username):
    with open("warnpoints.txt", "r") as f:
        p = json.loads(f.read())
    val = p[username]
    return val


def add_member(username, val=0):
    with open("warnpoints.txt", "r") as f:
        p = json.loads(f.read())
    try:
        p[username]
        return -1  # we do not expect this, since the user already exists
    except KeyError:
        p[username] = 0
        if val != 0:
            p[username] += val
        with open("warnpoints.txt", "w") as f:
            f.write(json.dumps(p))
    return 0


def add_warning_points(username):
    with open("warnpoints.txt", "r") as f:
        p = json.loads(f.read())
    p[username] += 1
    with open("warnpoints.txt", "w") as f:
        f.write(json.dumps(p))
    return p[username]


def minus_warning_points(username, val):
    with open("warnpoints.txt", "r") as f:
        p = json.loads(f.read())
    p[username] -= val
    if p[username] < 0:
        return -1
    with open("warnpoints.txt", "w") as f:
        f.write(json.dumps(p))
    return p[username]


@client.event
async def on_ready():
    print(f'Bot is ready!')
    print(f'Prefix: {cmd_prefix}')


@client.event
@commands.has_permissions(manage_messages=True)
async def on_message(message):
    ctx = await client.get_context(message)
    print(f'{message.author}: {message.content.lower()}')
    for word in fwords:
        if word in message.content.lower():
            print("WARNING: Filtered word detected")
            await message.delete()
            if not ("admin" in [y.name.lower()
                                for y in message.author.roles] or "owner"
                    in [y.name.lower() for y in message.author.roles]):
                await warn(ctx,
                           message.author,
                           reason='filtered word detected')
    await client.process_commands(message)


@client.event
async def on_member_join(member):
    print('on_member_join() running')
    try:
        readd_rejoin_member_warning_points(str(member))
    except KeyError:  # this means this guy has never been in the server
        add_member(str(member))


@client.event
async def on_member_remove(member):
    print('on_member_remove() running')
    add_left_member_warning_points(str(member))
    remove_member(str(member))


@client.command(help="Warn a user")
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    print('warn() running')
    print(member)
    ret = add_warning_points(str(member.id))
    if reason:
        await ctx.send(
            f'Warned {member.mention} for `{reason}`, user currently has `{ret}` warning points'
        )
    else:
        await ctx.send(
            f'Warned {member.mention}, user currently has `{ret}` warning points'
        )
    if ret == 5:
        await kick(ctx,
                   member,
                   reason='User has reached maximum warning points (kick)')
    elif ret == 10:
        await ban(ctx,
                  member,
                  reason='User has reached maximum warning points (ban)')


#@client.command()
#@commands.has_permissions(administrator=True)
#async def userinfo(ctx, member: discord.Member):
#	print("userinfo() running")


@client.command(help="Unwarn a user")
@commands.has_permissions(administrator=True)
async def unwarn(ctx, member: discord.Member, *, val):
    print('unwarn() running')
    print(member)
    ret = minus_warning_points(str(member), int(val))
    if ret == -1:
        await ctx.send(
            f'{member.mention} has smaller warning points than points to subtract, aborting!'
        )
    else:
        await ctx.send(
            f'-{val} in warning points of {member.mention}, user currently has {ret} warning points'
        )


@client.command(help="Refresh members list")
@commands.has_permissions(administrator=True)
async def members(ctx):
    users = dict()
    for guild in client.guilds:
        for member in guild.members:
            users[str(member.id)] = 0
            with open("warnpoints.txt", "w") as f:
                f.write(json.dumps(users))
    await ctx.send(f'Refreshed members list!')


@client.command(help="Kick a user")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    print('kick() running')
    await ctx.guild.kick(member)
    if reason:
        await ctx.send(f'User {member.mention} has been kicked for `{reason}`')
    else:
        await ctx.send(f'User {member.mention} has been kicked')
    dm = f"You were kicked from `MiniExploit's repower place` by {ctx.author.mention}"
    if reason:
        dm += f"for {reason}"
    channel = await member.create_dm()
    await channel.send(dm)


@client.command(help="Ban a user")
@commands.has_permissions(ban_members=True, manage_messages=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    print('ban() running')
    await ctx.guild.kick(member)
    if reason:
        await ctx.send(f'Banned {member.mention} for `{reason}`')
    else:
        await ctx.send(f'Banned `{member.mention}`')
    dm = f"You were banned from `MiniExploit's repower place` by {ctx.author.mention}"
    if reason:
        dm += f"for {reason}"
    channel = await member.create_dm()
    await channel.send(dm)


@client.command(help="Get current warning points of a user")
async def wpoints(ctx, member: discord.Member):
    print('wpoints() running')
    await ctx.send(
        f'{member.mention} currently has `{get_val(str(member.id))}` warning points'
    )


@client.command(help="Check if I'm still alive")
async def areyoualive(ctx):
    print('areyoualive() running')
    await ctx.send("I'm still alive!")


aboutme = """
Hi! I'm <@949243100788850748>, I was developed by <@935720424799625277>.
I was made specifically for `MiniExploit's repower place` for managing members and doing some stuffs.
"""


@client.command(help="About me")
async def aboutyou(ctx):
    await ctx.send(aboutme)


# start

keep_alive()
client.run(os.environ['BOT_TOKEN'])
