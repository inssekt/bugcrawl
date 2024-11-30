import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import tasks
import schedule
import time
from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

KEYWORDS = ["cyberdog", "couch uk rave"]

def fetch_vinted_listings():
    new_listings = []
    for keyword in KEYWORDS:
