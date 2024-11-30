import sqlite3

def setup_database():
    conn = sqlite3.connect("listings.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_listings (
            id TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()
    conn = sqlite3.connect("vinted_keywords.db")
    cursor = conn.cursor()
    
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        keyword TEXT UNIQUE)''')
    
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS keyword_channels (
                        keyword_id INTEGER, 
                        channel_id INTEGER, 
                        FOREIGN KEY (keyword_id) REFERENCES keywords (id),
                        PRIMARY KEY (keyword_id, channel_id))''')
    
    conn.commit()
    conn.close()

def is_listing_seen(listing_id):
    conn = sqlite3.connect("listings.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM seen_listings WHERE id = ?", (listing_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_listing_to_db(listing_id):
    conn = sqlite3.connect("listings.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO seen_listings (id)
        VALUES (?)
    """, (listing_id,))
    conn.commit()
    conn.close()


def save_keyword(keyword, channel_id):
    conn = sqlite3.connect("vinted_keywords.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM keywords WHERE keyword=?", (keyword,))
    result = cursor.fetchone()

    if result:
        keyword_id = result[0]
    else:
        cursor.execute("INSERT INTO keywords (keyword) VALUES (?)", (keyword,))
        keyword_id = cursor.lastrowid  

    
    cursor.execute("INSERT OR REPLACE INTO keyword_channels (keyword_id, channel_id) VALUES (?, ?)",
                   (keyword_id, channel_id))
    
    conn.commit()
    conn.close()


def get_channels_for_keyword(keyword):
    conn = sqlite3.connect("vinted_keywords.db")
    cursor = conn.cursor()

    cursor.execute('''SELECT c.channel_id 
                      FROM keywords k 
                      JOIN keyword_channels c ON k.id = c.keyword_id 
                      WHERE k.keyword = ?''', (keyword,))
    
    channels = cursor.fetchall()
    conn.close()

    return [channel[0] for channel in channels]  


def remove_keyword(keyword):
    conn = sqlite3.connect("vinted_keywords.db")
    cursor = conn.cursor()

    
    cursor.execute("DELETE FROM keyword_channels WHERE keyword_id = (SELECT id FROM keywords WHERE keyword = ?)", (keyword,))
    cursor.execute("DELETE FROM keywords WHERE keyword = ?", (keyword,))
    
    conn.commit()
    conn.close()


def get_keywords():
    conn = sqlite3.connect("vinted_keywords.db")
    cursor = conn.cursor()

    cursor.execute("SELECT keyword FROM keywords")
    keywords = cursor.fetchall()
    
    conn.close()

    return [keyword[0] for keyword in keywords]  