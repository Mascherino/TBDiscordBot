import json
from json.decoder import JSONDecodeError
import os
from sys import path
from discord.errors import Forbidden, HTTPException
import requests
import discord
from discord.ext import commands

TOKEN = ''
with open("TOKEN.txt","r") as f:
	TOKEN = f.readline()
	f.close()

client = discord.Client()
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!",intents=intents)

''' Variables '''

data = {}


''' Functions '''
def get_scholars():
	'''Iterate over scholar list, return dict of scholars and their MMR'''

	scholars = {}
	for ronin,scholar in data.items():
		url = "https://game-api.axie.technology/mmr/" + ronin
		r = requests.get(url)
		try:
			if r.status_code != 200:
				scholars[ronin] = "timeout"
			else:
				mmr = r.json()[0]['items'][1]['elo']
				scholars[ronin] = {}
				scholars[ronin]["mmr"] = mmr
				scholars[ronin]["name"] = scholar
		except KeyError:
			print("Something went wrong while getting scholar MMR, falling back to alternative url")
			return False
	scholars = dict(sorted(scholars.items(), key=lambda item: item[1]["mmr"], reverse=True))
	return scholars

def get_scholars_fallback():
	'''Fallback for get_scholars(), using a different API'''

	scholar_list =  ["0x1","0x2","0x3"]
	scholars = {}
	for scholar in scholar_list:
		r = requests.get("https://axiesworld.firebaseapp.com/updateSpecific?wallet=" + scholar)
		try:
			if r.status_code != 200:
				scholars[scholar] = "timeout"
			else:
				pvpData = r.json()['walletData']['pvpData']
				scholars[scholar] = pvpData['elo']
		except KeyError:
			pvpData = r.json()['pvpData']
			scholars[scholar] = pvpData['elo']
	return scholars

def prettify_scholar_dict(scholar_dict):
	'''Return pretty dict to print'''

	msg = ""
	for key,value in scholar_dict.items():
		if value["name"] != "":
			msg = msg + str(value["name"]) + " -- " + str(value["mmr"]) + " MMR\n"
		else:
			msg = msg + str(key) + " -- " + str(value["mmr"]) + " MMR\n"
	return msg

def read_json(file):
	''' Read JSON config file and write into data variable '''
	global data
	if os.path.isfile(file):
		with open(file,"r") as f:
			try:
				data = json.load(f)
			except JSONDecodeError:
				data = {}
		f.close()
		print("Successfully read config file.")

def save_json(file):
	''' Save data variable as JSON config file '''
	global data
	if os.path.isfile(file):
		with open(file,"w") as f:
			json.dump(data,f,sort_keys=True,indent=4)
		f.close()
		print("Successfully saved config file.")

@bot.event
async def on_ready():
	print(str(bot.user.name) + " has connected to Discord!")
	read_json("config.json")

@bot.command(name="addscholar")
#@commands.has_role("BotTest")
async def addscholar(ctx,ronin,name=""):
	'''
	Add scholar to database

	Parameters:
		ronin (str): ronin address scholar
		name (str): name of scholar [optional], defaults to empty

	Returns:
		Nothing, message is sent in channel
	'''
	global data
	if ronin != "":
		try:
			if not ronin in data:
				data[ronin] = name
				await ctx.send("Successfully added scholar.")
				save_json("config.json")
			else:
				await ctx.send("Error ronin address already in database.")
		except:
			await ctx.send("Could not add scholar.")
	else:
		await ctx.send("Error cannot add scholar without address")

@addscholar.error
async def addscholar_error(ctx,error):
	if isinstance(error,commands.CheckFailure):
		await ctx.send('You dont have the permission to use that command')

@bot.command(name="delscholar")
async def delscholar(ctx,attr):
	'''
	Delete scholar from database

	Parameters:
		attr (str): ronin address or name of scholar to delete

	Returns:
		Nothing, message is sent in channel
	'''
	global data
	try:
		if attr in data:
			removed_value = data.pop(attr)
			await ctx.send("Successfully removed scholar " + removed_value + "("+ attr +").")
			save_json("config.json")
		else:
			for key,value in data.items():
				if value == attr:
					removed_value = data.pop(key)
					await ctx.send("Successfully removed scholar " + removed_value + "("+ key+").")
					save_json("config.json")
					break
				else:
					await ctx.send("Error name / ronin address not found in database.")
	except Exception as e:
		print(e)
		await ctx.send("Error while trying to remove scholar.")

@bot.command(name="topscholars")
async def top_scholars(ctx):
	''' Post message in channel containing the top scholars sorted by descending MMR '''
	msg = await ctx.send(ctx.author.mention + """\nCalculating MMR...""")
	# em_msg = discord.Embed(title="Title",description="Desc",color=0x00ff00)
	# em_msg.add_field(name="Field1",value="test1",inline=False)
	# em_msg.add_field(name="Field2",value="test2",inline=True)
	# msg = await ctx.send(embed=em_msg)
	scholars = get_scholars()
	if not scholars:
		scholars_fallback = get_scholars_fallback()
		if not scholars_fallback:
			await ctx.send("Something went wrong getting scholar MMR, try again later.")
			return
	# await ctx.send(ctx.author.mention + """\nThe current top scholars are:\n""" + str(scholars))
	await msg.edit(content=ctx.author.mention + """\nThe current top scholars are:\n""" + prettify_scholar_dict(scholars))

@bot.command(name="addrole")
async def addrole(ctx,*args):
	'''
	Add role to specific user.

	Parameters:
		user (str): User that gets the role [optional], defaults to author
		role (str): role to add

	Returns:
		Nothing, message gets send in channel
	'''
	if len(args) == 2:
		role = args[1]
		user = discord.utils.get(ctx.guild.members,name=args[0])
	elif len(args) == 1:
		role = args[0]
		user = ctx.author
	var = discord.utils.get(ctx.guild.roles, name=role)
	if user == None:
		await ctx.send("Error user does not exist or is misspelled.")
		return
	elif var == None:
		await ctx.send("Error role does not exist or is misspelled.")
		return
	else:
		try:
			await user.add_roles(var)
			await ctx.send("success! User " + user.name + "#" +  user.discriminator + " now has role " + role + ".")
		except HTTPException:
			await ctx.send("Error failed to add the role.")
		except Forbidden:
			await ctx.send("Error no permission to add role.")

@bot.command(name="delrole")
async def delrole(ctx,*args):
	'''
	Add role to specific user.

	Parameters:
		user (str): User to remove role from [optional], defaults to author
		role (str): role to remove

	Returns:
		Nothing, message gets send in channel
	'''
	if len(args) == 2:
		role = args[1]
		user = discord.utils.get(ctx.guild.members,name=args[0])
	elif len(args) == 1:
		role = args[0]
		user = ctx.author
	var = discord.utils.get(ctx.guild.roles, name=role)
	if user == None:
		await ctx.send("Error user does not exist or is misspelled.")
		return
	elif var == None:
		await ctx.send("Error role does not exist or is misspelled.")
		return
	else:
		if var in user.roles:
			try:
				await user.remove_roles(var)
				await ctx.send("Success! User " + user.name + "#" +  user.discriminator + " no longer has role " + role + ".")
			except HTTPException:
				await ctx.send("Error failed to remove the role.")
			except Forbidden:
				await ctx.send("Error no permission to remove role.")
		else:
			await ctx.send("Error User " + user.name + " does not have role " + var)


bot.run(TOKEN)


