import streamlit as st 
import requests
import hashlib 
import time 
import pandas as pd 
from datetime import datetime
from config import PUBLIC_KEY, PRIVATE_KEY

# Return a dict of authentication parameters for the API request
def get_auth_params():
    ts = str(time.time())
    hash_digest = hashlib.md5((ts + PRIVATE_KEY + PUBLIC_KEY).encode()).hexdigest()
    return {"ts": ts, "apikey": PUBLIC_KEY, "hash": hash_digest}

# Fetch and return a sorted list of unique Marvel Character names (up to 2000), using pagination and caching the result
def fetch_character_list():
    url = "https://gateway.marvel.com/v1/public/characters"
    all_names = []
    for offset in range (0, 2000, 100):
        params = {**get_auth_params(), "limit": 100, "offset": offset}
        res = requests.get(url, params=params).json()
        results = res["data"]["results"]
        if not results:
            break
        all_names.extend([char["name"] for char in results])
    return sorted(set(all_names))

# Retrieve and return the character ID for a given character name
def get_character_id(character_name):
    url = "https://gateway.marvel.com/v1/public/characters"
    params = {**get_auth_params(), "name": character_name}
    res = requests.get(url, params=params).json()
    results = res["data"]["results"]
    return results[0]["id"] if results else None 

# Retrieve a list of comics for a given character ID within a specified year range, ordered by latest onsale date
def get_comics(character_id, start_year, end_year, limit=10):
    url = f"https://gateway.marvel.com/v1/public/characters/{character_id}/comics"
    params = {
        **get_auth_params(), 
        "limit": limit,
        "orderBy": "-onsaleDate", 
        "dateRange": f"{start_year}-01-01,{end_year}-12-31"
    }
    res = requests.get(url, params=params).json()
    return res["data"]["results"] 

# Streamlit UI
st.title("Marvel Comics Recommender Engine")

character_list = fetch_character_list()
character_input = st.selectbox(
    "Choose a Marvel Character:",
    character_list,
    index=None,
    placeholder="Seach or Select a character..."
)

decade = st.selectbox(
    "Choose a timeframe for the comics you like to see:",
    ["1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
)

decade_years = {
    "1940s": (1940, 1949),
    "1950s": (1950, 1959),
    "1960s": (1960, 1969),
    "1970s": (1970, 1979),
    "1980s": (1980, 1989),
    "1990s": (1990, 1999),
    "2000s": (2000, 2009),
    "2010s": (2010, 2019),
    "2020s": (2020, datetime.now().year)
}

if character_input and decade:
    char_id = get_character_id(character_input)
    if char_id:
        start, end = decade_years[decade]
        comics = get_comics(char_id, start, end)

        if comics:
            st.subheader(f"Top Comic Picks for {character_input} ({decade})")

            comic_data = []
            for comic in comics:
                title = comic["title"]
                description = comic.get("description", "No description")
                thumbnail = comic["thumbnail"]
                img_url = f"{thumbnail['path']}.{thumbnail['extension']}"
                urls = comic.get("urls", [])
                detail_url = next((u["url"] for u in urls if u["type"] == "detail"), "")

                st.markdown(f"### [{title}]({detail_url})")
                st.markdown(description)
                st.image(img_url, width=300)
                st.markdown("---")

                comic_data.append({
                    "Title": title,
                    "Description": description,
                    "Image URL": img_url,
                    "Detail Page": detail_url
                })

            # Downloadable CSV
            df = pd.DataFrame(comic_data)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Recommendations as CSV",
                data=csv,
                file_name=f"{character_input}_{decade}_comics.csv",
                mime="text/csv"
            )
        else:
            st.info("No comics found for that character and timeframe.")
    else:
        st.error("Character not found. Please try another.")
