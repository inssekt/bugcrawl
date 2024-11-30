import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import db  
import vinted  
from scrapers.vinted_scraper import VintedScraper


load_dotenv()


intents = discord.Intents.default()
intents.message_content = True 
intents.guilds = True


bot = commands.Bot(command_prefix='/', intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1311344458822058077  


vinted_scraper = VintedScraper()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    
    db.setup_database()
    periodic_scraping.start()  



@bot.command()
async def createkeyword(ctx, keyword: str):
    
    if ctx.author.guild_permissions.administrator:
        guild = ctx.guild

        
        existing_channel = discord.utils.get(guild.text_channels, name=keyword)
        if existing_channel:
            await ctx.send(f"The channel for keyword '{keyword}' already exists!")
        else:
            
            new_channel = await guild.create_text_channel(keyword)

            
            db.save_keyword(keyword, new_channel.id)

            await ctx.send(f"Keyword '{keyword}' created and new channel '{new_channel.name}' has been made!")
    else:
        await ctx.send("You do not have permission to create a keyword. You must be an administrator.")



async def send_to_discord(message_data):
    if 'image_url' not in message_data:
        print(f"Error: 'image' not found for listing {message_data['title']}")
        message_data['image'] = "https://via.placeholder.com/150"  
    
    
    embed = discord.Embed(
        title=message_data['title'],
        description=f"**Price**: {message_data['price']}\n**Brand**: {message_data['brand']}",  
        url=message_data['link'],  
        color=discord.Color.blue()
    )
    
    
    embed.set_image(url=message_data['image_url'])

    
    channels = db.get_channels_for_keyword(message_data['keyword'])
    
    for channel_id in channels:
        
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)
            print(f"Sent message to channel: {message_data['title']}")  
        else:
            print(f"Error: Could not find channel {channel_id} for keyword '{message_data['keyword']}'.")



@tasks.loop(minutes=1)  
async def periodic_scraping():
    
    keywords = db.get_keywords()

    for keyword in keywords:
        
        listings = vinted_scraper.fetch_listings(keyword)

        if listings:
            for listing in listings:
                message_data = {
                    'title': listing['title'],
                    'price': listing['price'],
                    'brand': listing['brand'],
                    'link': listing['link'],
                    'image_url': listing['image'],
                    'keyword': keyword  
                }
                
                await send_to_discord(message_data)



bot.run(TOKEN)