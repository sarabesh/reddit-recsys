# 🧠 Reddit-RecSys  
## Multimodal Recommendation System (WIP)

This project is a real-time multimodal recommendation system built on top of Reddit data. It processes image-caption pairs using **CLIP** to create joint embeddings, stores them in **Qdrant**, and supports semantic retrieval based on text or image input.

---

## 🔧 Key Components

- 🔄 **Ingestion**: Reddit image posts and captions pulled from multiple subreddits
- 🧠 **Embedding**: Featurization using `open-clip-torch`
- 🗃️ **Vector Storage**: Stored and queried via [Qdrant](https://qdrant.tech)
- 🪄 **Orchestration**: Apache Airflow (deployed via Helm on Kubernetes)
- 🔍 **Retrieval**: ANN-based search with image or text queries

---

> ⚠️ **Work In Progress** — Setup, DAGs, and usage instructions will be added soon.
