import torch
import clip
from PIL import Image
import scripts.config as config
from qdrant_client import QdrantClient
import matplotlib.pyplot as plt
import numpy as np
import os


# --- Config ---
COLLECTION_NAME = "reddit_posts"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMAGE_ROOT = "data/images"

# --- Load CLIP ---
model, preprocess = clip.load("ViT-B/32", device=DEVICE)

# --- Init Qdrant ---
client = QdrantClient(url=config.QDRANT_HOST, port=config.QDRANT_PORT, api_key=config.QDRANT_API_KEY)

# --- Embed Query ---
def get_query_vector(text=None, image_path=None):
    if text:
        tokens = clip.tokenize([text]).to(DEVICE)
        with torch.no_grad():
            text_feat = model.encode_text(tokens)
        vector = text_feat / text_feat.norm(dim=-1, keepdim=True)
    elif image_path:
        image = preprocess(Image.open(image_path)).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            img_feat = model.encode_image(image)
        vector = img_feat / img_feat.norm(dim=-1, keepdim=True)
    else:
        raise ValueError("Provide either `text` or `image_path`")
    
    return vector.cpu().numpy().astype("float32")[0]

# --- Query Qdrant and Display ---
def search_and_display(query_vector,text_query, k=5):

    # Search in Qdrant, using HNSW for fast approximate nearest neighbor search
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=k
    ).points

    fig, axs = plt.subplots(1, k, figsize=(4*k, 5))
    if k == 1:
        axs = [axs]

    for i, (hit, ax) in enumerate(zip(results, axs)):
        img_path = os.path.join("data", hit.payload["image_path"])
        caption = hit.payload["caption"]

        try:
            image = Image.open(img_path)
            ax.imshow(image)
            ax.set_title(f"#{i+1} - Score: {hit.score:.2f}", fontsize=10)
            ax.axis('off')
            ax.set_xlabel(caption[:60] + "..." if len(caption) > 60 else caption, fontsize=8)
        except Exception as e:
            ax.text(0.5, 0.5, f"Error\n{e}", ha='center', va='center')
            ax.axis('off')
    plt.suptitle(text_query, fontsize=16)
    # plt.tight_layout()
    plt.show()
# --- Run a test query ---
if __name__ == "__main__":
    # TEXT example:
    text_query = "animals in nature"
    print(f"\n🔍 Querying with text: {text_query}")
    vec = get_query_vector(text=text_query)
    # IMAGE example:
    # vec = get_query_vector(image_path="sample_inputs/SampleGatesHeader.jpg")
    search_and_display(vec,text_query)
