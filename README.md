# Information Retrieval Models and Techniques

This repository contains my assignments and projects related to the Information Retrieval (IR) subject. The main objective of these assignments is to explore and implement different IR models and techniques for document retrieval, ranking, and content organization.

## Models and Techniques

### 1. **Ranking using IDF and TF-IDF**
   - Implemented traditional ranking mechanisms based on **Inverse Document Frequency (IDF)** and **Term Frequency-Inverse Document Frequency (TF-IDF)**.
   - **TF-IDF** is used to measure the relevance of a document based on the frequency of terms in a document relative to the entire document corpus.
   - The ranking is done by calculating the cosine similarity between query vectors and document vectors.

### 2. **Cosine Similarity**
   - Built a ranking system using **Cosine Similarity** to measure the similarity between the query and document vectors.
   - The cosine of the angle between vectors is computed to evaluate document relevance.

### 3. **BIM Model (Boolean Information Model)**
   - Developed a Boolean model for document retrieval, focusing on exact matches between queries and document terms.
   - Boolean operators such as AND, OR, and NOT are applied to search queries for matching documents.

### 4. **NOLM (Non-Linear Model)**
   - Implemented a **Non-Linear Model** to evaluate document relevance based on more complex relationships and term dependencies.
   - Used advanced ranking algorithms beyond traditional linear models.

### 5. **PNM (Probabilistic Network Model)**
   - Developed a **Probabilistic Network Model (PNM)** to calculate document relevance based on probabilistic inference techniques.
   - The model evaluates document-query relevance through a belief network structure.

### 6. **Guided Structure Model**
   - Designed a **Guided Structure Model** for structured document retrieval.
   - This model includes hierarchical content organization and navigation features to assist users in retrieving relevant documents.

### 7. **Hypertext Model**
   - Built a **Hypertext Model** for document retrieval, focusing on the interlinking of content and navigation.
   - This model uses hypertext links to guide users through related documents and information.



## Requirements

- Python 3.x
- Flask (for search API)
- math (for mathematical functions)
- docx (for document processing)
