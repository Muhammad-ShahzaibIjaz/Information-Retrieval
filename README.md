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

### 3. **BIM Model (Binary Independence Model)**
   - Developed the **Binary Independence Model (BIM)**, which evaluates document relevance based on binary independence assumptions between terms.
   - In this model, the presence or absence of a term in a document is considered to be independent of other terms, and document relevance is computed using probabilities.
   - The model is typically used in probabilistic information retrieval systems, such as Okapi BM25.

### 4. **NOLM (Non-Overlapped List Model)**
   - Implemented the **Non-Overlapped List Model (NOLM)** for evaluating document relevance.
   - The NOLM focuses on how terms in a query map to non-overlapping lists of document IDs, providing a measure of relevance based on the frequency and distribution of terms across documents.
   - This model handles relationships and dependencies between terms, offering a more nuanced ranking mechanism.

### 5. **PNM (Proximal Nodes Model)**
   - Developed the **Proximal Nodes Model (PNM)** to calculate document relevance using the proximity of terms in a document.
   - The model uses the proximity of relevant terms within a document to influence the ranking, with the assumption that documents where terms appear closer together are more relevant to the query.
   - This model enhances retrieval by considering the spatial relationships of terms within documents.

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
