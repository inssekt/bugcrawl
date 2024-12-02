import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import db  
from scrapers.vinted_scraper import VintedScraper
from scrapers.depop_scraper import DepopScraper
from scrapers.mercarijp_scraper import MercariJPScraper
import asyncio
import datetime

intents = discord.Intents.default()
intents.message_content = True 
intents.guilds = True


bot = commands.Bot(command_prefix='/', intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1311344458822058077  


vinted_scraper = VintedScraper()
depop_scraper = DepopScraper()
mercarijp_scraper = MercariJPScraper()

scrapers = {
    "vinted": VintedScraper(),
    "depop": DepopScraper(),
    "mercarijp": MercariJPScraper()
}


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()

    db.setup_database()
    asyncio.create_task(start_scraping()) 
    
async def start_scraping():
    while True:
        try:
            await scrape()
        except Exception as e:
            print(f"Error during scraping: {e}")
        await asyncio.sleep(60)

@bot.tree.command(name="createkeyword", description="Create a new keyword to periodically scrape from a platform")
async def createkeyword(
    interaction: discord.Interaction, 
    keyword: str, 
    platform: str
):
    """
    Command to create a new keyword and channel under the respective platform category.
    """
    if interaction.user.guild_permissions.administrator:
        guild = interaction.guild
        category_name = platform.capitalize()  
        category = discord.utils.get(guild.categories, name=category_name)

        if not category:
            category = await guild.create_category(category_name)

        existing_channel = discord.utils.get(guild.text_channels, name=keyword, category=category)
        if existing_channel:
            await interaction.response.send_message(f"The channel for keyword '{keyword}' already exists under the platform '{platform}'!")
        else:
            new_channel = await guild.create_text_channel(keyword, category=category)
            db.save_keyword(keyword, platform, new_channel.id)
            await interaction.response.send_message(f"Keyword '{keyword}' created under platform '{platform}' with channel '{new_channel.name}'!")
    else:
        await interaction.response.send_message("You do not have permission to create a keyword. You must be an administrator.")

@createkeyword.error
async def createkeyword_error(interaction: discord.Interaction, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await interaction.response.send_message("Error: You need to specify a keyword and platform! Usage: `/createkeyword <keyword> <platform>`")
    else:
        await interaction.response.send_message(error)

async def send_to_discord(message_data): 
    if 'title' not in message_data:
        message_data['title'] = "Couldn't fetch title"
        print(f"Error: 'title' not found for listing {message_data['title']}")
    if 'price' not in message_data:
        message_data['price'] = "Couldn't fetch price"
        print(f"Error: 'price' not found for listing {message_data['title']}")
    if 'brand' not in message_data:
        message_data['brand'] = "Couldn't fetch brand"
        print(f"Error: 'brand' not found for listing {message_data['title']}")
    if 'link' not in message_data:
        message_data['link'] = "google.com"
        print(f"Error: 'link' not found for listing {message_data['title']}")
    if 'image_url' not in message_data:
        print(f"Error: 'image' not found for listing {message_data['title']}")
        message_data['image_url'] = "https://via.placeholder.com/150" 

    embedColor = discord.Colour.greyple()
    if message_data['platform'] == "vinted":
        embedColor = discord.Colour.blurple()
    elif message_data['platform'] == "depop":
        embedColor = discord.Colour.dark_red()
    elif message_data['platform'] == "mercarijp":
        embedColor = discord.Colour.red()

    embed = discord.Embed(
        title="New Listing",
        url=message_data['link'],  
        color=embedColor,
        timestamp=datetime.datetime.now()
        
    )

    embed.add_field(name="Title",
        value=message_data['title'],
        inline=False)
    embed.add_field(name="Price",
        value=message_data['price'],
        inline=True)
    embed.add_field(name="Brand",
        value=message_data['brand'],
        inline=True)
    embed.set_footer(text="Scraped by bugcrawl",
        icon_url="https://img.freepik.com/premium-vector/ladybug-with-closed-shell-beetle-cartoon-bug-design-flat-vector-illustration-isolated-white-background_257455-3194.jpg")

    embed.set_image(url=message_data['image_url'])

    embed.set_footer(text="Scraped by bugcrawl",
                 icon_url="https://img.freepik.com/premium-vector/ladybug-with-closed-shell-beetle-cartoon-bug-design-flat-vector-illustration-isolated-white-background_257455-3194.jpg")


    channels = db.get_channels_for_keyword(message_data['keyword'], message_data['platform'])
    for channel_id in channels:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)
            print(f"Sent message to channel: {message_data['title']}")
        else:
            print(f"Error: Could not find channel {channel_id} for keyword '{message_data['keyword']}' on platform '{message_data['platform']}'.")
            
            db.remove_channel_for_keyword(message_data['keyword'], message_data['platform'], channel_id)

async def scrape():
    keywords = db.get_keywords()  
    platform_keywords = {}
    for keyword, platform in keywords:
        platform_keywords.setdefault(platform, []).append(keyword)
    platform_tasks = []
    for platform, keywords in platform_keywords.items():
        platform_task = asyncio.create_task(scrape_platform(platform, keywords))  
        platform_tasks.append(platform_task)
    await asyncio.gather(*platform_tasks)

async def scrape_platform(platform, keywords):
    print(f"Starting to scrape {platform}...")

    
    tasks = [scrape_keyword(keyword, platform) for keyword in keywords]

    
    await asyncio.gather(*tasks)

async def scrape_keyword(keyword, platform):
    print(f"Scraping {platform} for keyword: {keyword}")

    channel_ids = db.get_channels_for_keyword(keyword, platform)
    for channel_id in channel_ids:
        channel = bot.get_channel(channel_id)
        if not channel:
            print(f"Channel with ID {channel_id} for keyword '{keyword}' on platform '{platform}' no longer exists.")
            db.remove_channel_for_keyword(keyword, platform, channel_id)
            continue

        if platform == "vinted":
            listings = await vinted_scraper.fetch_listings(keyword)
        elif platform == "depop":
            listings = await depop_scraper.fetch_listings(keyword)
        elif platform == "mercarijp":
            listings = await mercarijp_scraper.fetch_listings(keyword)
        else:
            return  
        if listings:
            for listing in listings:
                message_data = {
                    'title': listing['title'],
                    'price': listing['price'],
                    'brand': listing['brand'],
                    'link': listing['link'],
                    'image_url': listing['image'],
                    'keyword': keyword,
                    'platform': platform,
                }
                await send_to_discord(message_data)


bot.run(TOKEN)