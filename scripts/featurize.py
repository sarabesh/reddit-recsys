import os
import torch
import clip
import config as config
import pandas as pd
import numpy as np
from PIL import Image
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

# --- Config ---
CSV_INPUT_PATH = "data/image_captions.csv"
IMAGE_ROOT = "data/images"
EMBEDDING_OUTPUT_DIR = "embeddings"  # <- now outside /data
VECTOR_SIZE = 512  # CLIP ViT-B/32 outputs 512-dimensional vectors
COLLECTION_NAME = "reddit_posts" # Use the collection name from config

# --- Init Qdrant ---
client = QdrantClient(url=config.QDRANT_HOST, port=config.QDRANT_PORT, api_key=config.QDRANT_API_KEY)
# Check if collection exists, if not create it     
if client.collection_exists(collection_name=COLLECTION_NAME)==False:
    print(f"⚠️ Collection '{COLLECTION_NAME}' does not exist. Creating it now...")  
    client.create_collection(
        collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
)

# --- Load CLIP ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# --- Load Caption CSV ---
df = pd.read_csv(CSV_INPUT_PATH)

# --- Prepare output folders ---
os.makedirs(EMBEDDING_OUTPUT_DIR, exist_ok=True)

# --- Featurize each (image, caption) pair ---
embeddings = []
metadata = []

for i, row in tqdm(df.iterrows(), total=len(df)):
    rel_image_path = row["image_path"]
    caption = row["caption"][:300]  # Limit caption to 300 characters, as CLIP can handle up to 77 tokens, which is roughly 300 characters. Change this later if needed.
    full_image_path = os.path.join("data", rel_image_path)

    if not os.path.exists(full_image_path):
        print(f"⚠️ Image not found: {full_image_path}")
        continue

    try:
        image = preprocess(Image.open(full_image_path)).unsqueeze(0).to(device)
        text = clip.tokenize([caption]).to(device)

        with torch.no_grad():
            img_feat = model.encode_image(image)
            txt_feat = model.encode_text(text)
            combined = (img_feat + txt_feat) / 2
            combined /= combined.norm(dim=-1, keepdim=True)

        vector = combined.cpu().numpy()[0] # Combined vector for image and caption

        # embeddings.append(combined.cpu().numpy()[0])
        # metadata.append({"image_path": rel_image_path, "caption": caption})
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=i,
                vector=vector,
                payload={
                    "image_path": row["image_path"],
                    "caption": caption
                }
            )]
        )

    except Exception as e:
        print(f"❌ Failed to process {rel_image_path}: {e}")

# --- Save vectors and metadata ---
# vector_path = os.path.join(EMBEDDING_OUTPUT_DIR, VECTOR_FILE_NAME)
# metadata_path = os.path.join(EMBEDDING_OUTPUT_DIR, METADATA_FILE_NAME)

# np.save(vector_path, np.stack(embeddings))
# pd.DataFrame(metadata).to_csv(metadata_path, index=False)

# print(f"\n✅ Saved {len(embeddings)} vectors to: {vector_path}")
# print(f"📝 Metadata saved to: {metadata_path}")


print(f"✅ Uploaded {len(df)} vectors directly to Qdrant.")