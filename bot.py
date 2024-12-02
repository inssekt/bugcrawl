import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import db  
from scrapers.vinted_scraper import VintedScraper
from scrapers.depop_scraper import DepopScraper

intents = discord.Intents.default()
intents.message_content = True 
intents.guilds = True


bot = commands.Bot(command_prefix='/', intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1311344458822058077  


vinted_scraper = VintedScraper()
depop_scraper = DepopScraper()

scrapers = {
    "vinted": VintedScraper(),
    "depop": DepopScraper(),
}


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    
    db.setup_database()
    periodic_scraping.start()  



@bot.command(help="Create a new keyword and assign it to a platform.\nUsage: /createkeyword <keyword> <platform>")
async def createkeyword(ctx, keyword: str, platform: str):
    """
    Command to create a new keyword and channel under the respective platform category.
    """
    if ctx.author.guild_permissions.administrator:
        guild = ctx.guild

        
        category_name = platform.capitalize()  
        category = discord.utils.get(guild.categories, name=category_name)
        
        
        if not category:
            category = await guild.create_category(category_name)
            await ctx.send(f"Category '{category_name}' created.")

        
        existing_channel = discord.utils.get(guild.text_channels, name=keyword, category=category)
        if existing_channel:
            await ctx.send(f"The channel for keyword '{keyword}' already exists under the platform '{platform}'!")
        else:
            
            new_channel = await guild.create_text_channel(keyword, category=category)

            
            db.save_keyword(keyword, platform, new_channel.id)

            await ctx.send(f"Keyword '{keyword}' created under platform '{platform}' with channel '{new_channel.name}'!")
    else:
        await ctx.send("You do not have permission to create a keyword. You must be an administrator.")



@createkeyword.error
async def createkeyword_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument) and error.param.name == 'keyword':
        await ctx.send("Error: You need to specify a keyword! Usage: `/createkeyword <keyword>`")
    else:
        await ctx.send("An unexpected error occurred while processing your command. Usage: `/createkeyword <keyword>`")



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

    
    channels = db.get_channels_for_keyword(message_data['keyword'], message_data['platform'])

    for channel_id in channels:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)
            print(f"Sent message to channel: {message_data['title']}")
        else:
            print(f"Error: Could not find channel {channel_id} for keyword '{message_data['keyword']}' on platform '{message_data['platform']}'.")
            
            db.remove_channel_for_keyword(message_data['keyword'], message_data['platform'], channel_id)



@tasks.loop(minutes=1)  
async def periodic_scraping():
    
    keywords = db.get_keywords()

    for keyword, platform in keywords:
        
        channel_ids = db.get_channels_for_keyword(keyword, platform)

        for channel_id in channel_ids:
            
            channel = bot.get_channel(channel_id)

            
            if not channel:
                print(f"Channel with ID {channel_id} for keyword '{keyword}' on platform '{platform}' no longer exists.")
                db.remove_channel_for_keyword(keyword, platform, channel_id)  
                continue  
            
            
            if platform == "vinted":
                listings = vinted_scraper.fetch_listings(keyword)
            elif platform == "depop":
                listings = depop_scraper.fetch_listings(keyword)
            else:
                continue  
            
            
            if listings:
                for listing in listings:
                    message_data = {
                        'title': listing['title'],
                        'price': listing['price'],
                        'brand': listing['brand'],
                        'link': listing['link'],
                        'image_url': listing['image'],
                        'keyword': keyword,
                        'platform': platform  
                    }

                    
                    await send_to_discord(message_data)



bot.run(TOKEN)