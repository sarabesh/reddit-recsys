import praw
import requests
import re
import os
import csv
import config

# --- Connect to Reddit ---
print(f"🔗 Connecting to Reddit API with user agent: {config.REDDIT_USER_AGENT}")
r = praw.Reddit(
    client_id=config.REDDIT_CLIENT_ID,
    client_secret=config.REDDIT_CLIENT_SECRET,
    user_agent=config.REDDIT_USER_AGENT,
)

# --- Subreddits to scrape ---
subreddits = [
    "EarthPorn",
    "CityPorn",
    "SkyPorn",
    "BeachPorn",
    "WaterPorn",
    "ArtPorn"
]

# --- Output paths ---
data_dir = os.path.join(".", "data")
image_dir = os.path.join(data_dir, "images")
csv_path = os.path.join(data_dir, "image_captions.csv")

os.makedirs(image_dir, exist_ok=True)

# --- Prepare CSV ---
write_header = not os.path.exists(csv_path)
csv_file = open(csv_path, mode="a", newline="", encoding="utf-8")
csv_writer = csv.writer(csv_file)
if write_header:
    csv_writer.writerow(["image_path", "caption", "subreddit"])

# --- Counters ---
downloaded = 0
skipped = 0

# --- Scrape each subreddit ---
for sub_name in subreddits:
    print(f"\n📥 Scraping r/{sub_name}...")
    subreddit = r.subreddit(sub_name)
    top_posts = subreddit.top(limit=3000)  # Fetch top 3000 posts

    for post in top_posts:
        url = post.url

        # Skip non-image posts
        if not url.lower().endswith((".jpg", ".jpeg", ".png")):
            skipped += 1
            continue

        # Sanitize filename
        file_name = re.sub(r"[^\w\-.]", "_", url.split("/")[-1])
        if "." not in file_name:
            file_name += ".jpg"

        rel_path = os.path.join("images", file_name)
        full_path = os.path.join(data_dir, rel_path)

        if os.path.exists(full_path):
            print(f"⚠️ Already exists: {rel_path}")
            skipped += 1
            continue

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(full_path, "wb") as f:
                f.write(response.content)
            downloaded += 1
            print(f"✅ Downloaded: {rel_path}")

            # Write row to CSV
            csv_writer.writerow([rel_path, post.title, sub_name])

        except Exception as e:
            print(f"❌ Failed: {url} - {e}")
            skipped += 1

# --- Cleanup ---
csv_file.close()

# --- Summary ---
print("\n📊 Download Summary:")
print(f"✔️ Images downloaded: {downloaded}")
print(f"⏭️ Skipped (non-images/exists/errors): {skipped}")
print(f"📦 Total processed: {downloaded + skipped}")
print(f"📝 CSV saved to: {csv_path}")
