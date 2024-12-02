import sqlite3

# Function to set up the database and create necessary tables
def setup_database():
    conn = sqlite3.connect("bugcrawl.db")
    cursor = conn.cursor()

    # Create table for seen listings (used to track listings that have been scraped)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_listings (
            id TEXT PRIMARY KEY
        )
    """)

    # Create table for keywords and platforms
    cursor.execute('''CREATE TABLE IF NOT EXISTS keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT UNIQUE,
                        platform TEXT)''')

    # Create table for storing keyword-channel relationships
    cursor.execute('''CREATE TABLE IF NOT EXISTS keyword_channels (
                        keyword_id INTEGER, 
                        channel_id INTEGER,
                        platform TEXT,
                        FOREIGN KEY (keyword_id) REFERENCES keywords (id),
                        PRIMARY KEY (keyword_id, channel_id, platform))''')

    conn.commit()
    conn.close()


# Function to check if a listing has been seen before (by its listing ID)
def is_listing_seen(listing_id):
    conn = sqlite3.connect("bugcrawl.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM seen_listings WHERE id = ?", (listing_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


# Function to save a listing ID in the database to mark it as seen
def save_listing_to_db(listing_id):
    conn = sqlite3.connect("bugcrawl.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO seen_listings (id)
        VALUES (?)
    """, (listing_id,))
    conn.commit()
    conn.close()


# Function to save a keyword, its associated platform, and the channel ID
def save_keyword(keyword, platform, channel_id):
    conn = sqlite3.connect("bugcrawl.db")
    cursor = conn.cursor()

    # Check if the keyword and platform combination already exists
    cursor.execute("SELECT id FROM keywords WHERE keyword=? AND platform=?", (keyword, platform))
    result = cursor.fetchone()

    if result:
        keyword_id = result[0]
    else:
        # If it doesn't exist, insert the new keyword and platform into the keywords table
        cursor.execute("INSERT INTO keywords (keyword, platform) VALUES (?, ?)", (keyword, platform))
        keyword_id = cursor.lastrowid

    # Save the keyword-channel-platform relationship
    cursor.execute("""
        INSERT OR REPLACE INTO keyword_channels (keyword_id, channel_id, platform)
        VALUES (?, ?, ?)
    """, (keyword_id, channel_id, platform))

    conn.commit()
    conn.close()


# Function to get the list of channel IDs for a given keyword and platform
def get_channels_for_keyword(keyword, platform):
    conn = sqlite3.connect("bugcrawl.db")
    cursor = conn.cursor()

    # Retrieve channels associated with the given keyword and platform
    cursor.execute('''SELECT c.channel_id 
                      FROM keywords k 
                      JOIN keyword_channels c ON k.id = c.keyword_id 
                      WHERE k.keyword = ? AND k.platform = ?''', (keyword, platform))
    
    channels = cursor.fetchall()
    conn.close()

    return [channel[0] for channel in channels]


# Function to remove a keyword, its associated channels, and platform
def remove_keyword(keyword, platform):
    conn = sqlite3.connect("bugcrawl.db")
    cursor = conn.cursor()

    # Remove the keyword-channel relationship
    cursor.execute('''DELETE FROM keyword_channels 
                      WHERE keyword_id = (SELECT id FROM keywords WHERE keyword = ? AND platform = ?)''', (keyword, platform))

    # Remove the keyword entry
    cursor.execute("DELETE FROM keywords WHERE keyword = ? AND platform = ?", (keyword, platform))

    conn.commit()
    conn.close()


# Function to get all the keywords from the database
def get_keywords():
    conn = sqlite3.connect("bugcrawl.db")
    cursor = conn.cursor()

    cursor.execute("SELECT keyword, platform FROM keywords")
    keywords = cursor.fetchall()

    conn.close()

    return [(keyword[0], keyword[1]) for keyword in keywords]  # Return a list of (keyword, platform) tuples


# Function to get the keyword and platform associated with a channel ID
def get_keyword_for_channel(channel_id):
    conn = sqlite3.connect("bugcrawl.db")
    cursor = conn.cursor()

    cursor.execute('''SELECT k.keyword, k.platform 
                      FROM keyword_channels c 
                      JOIN keywords k ON k.id = c.keyword_id 
                      WHERE c.channel_id = ?''', (channel_id,))
    
    result = cursor.fetchone()
    conn.close()

    return result  # Returns a tuple (keyword, platform) or None if not found

def remove_channel_for_keyword(keyword, platform, channel_id):
    """
    Removes the association of a channel with a keyword and platform from the database.
    """
    conn = sqlite3.connect("bugcrawl.db")
    cursor = conn.cursor()

    # Get the platform's category (platform is assumed to be part of the keyword)
    cursor.execute('''
        SELECT k.id
        FROM keywords k
        WHERE k.keyword = ? AND k.platform = ?
    ''', (keyword, platform))

    keyword_id_row = cursor.fetchone()

    if keyword_id_row:
        keyword_id = keyword_id_row[0]

        # Remove the channel_id from the keyword_channels table
        cursor.execute('''
            DELETE FROM keyword_channels 
            WHERE keyword_id = ? AND channel_id = ?
        ''', (keyword_id, channel_id))
        
        conn.commit()
        print(f"Channel ID {channel_id} removed for keyword '{keyword}' and platform '{platform}'.")
    else:
        print(f"Keyword '{keyword}' with platform '{platform}' not found in the database.")

    conn.close()