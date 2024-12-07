import os
import string
from math import sqrt
from docx import Document
from collections import defaultdict, Counter
from flask import Flask, request, jsonify
from flask_cors import CORS



app = Flask(__name__)
CORS(app)


class SearchEngine:
    def __init__(self, folder_path='Documents'):
        self.folder_path = folder_path
        self.extracted_documents, self.content_index, self.title_index, self.author_index, self.doc_lengths, self.search_terms = self.setup_search_engine()

    def setup_search_engine(self):
        extracted_documents = self.document_extractor()
        extracted_content = self.extract_fullContext_from_documents(extracted_documents)
        extracted_titles = self.extract_titles_from_documents(extracted_documents)
        extracted_authors = self.extract_author_from_documents(extracted_documents)
        
        content_index, doc_lengths, search_terms = self.build_index(extracted_content)
        title_index, _, _ = self.build_index(extracted_titles)
        author_index, _, _ = self.build_index(extracted_authors)

        return extracted_documents, content_index, title_index, author_index, doc_lengths, search_terms

    def extract_text_from_documents(self, file_path):
        document = Document(file_path)
        doc_data = {'title': "", 'author': "", "content": ""}

        paragraphs = (p.text.strip() for p in document.paragraphs if p.text.strip())
        for text in paragraphs:
            if not doc_data['title']:
                doc_data['title'] = text
            elif text.startswith("Author:"):
                doc_data['author'] = text[7:].strip()
            else:
                doc_data['content'] += f" {text}"

        content = f"{doc_data['title']} {doc_data['author']} {doc_data['content']}".replace("Abstract", "").strip()
        doc_data['content'] = content
        return doc_data

    def document_extractor(self):
        documents = []
        for file_name in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, file_name)
            if not (os.path.isfile(file_path) and file_name.endswith('.docx')):
                continue

            doc_data = self.extract_text_from_documents(file_path)
            doc_data['file_name'] = file_path
            documents.append(doc_data)

        return documents

    def extract_fullContext_from_documents(self, documents):
        return [
            f"Title: {doc['title']}\nAuthor: {doc['author']}\nContent: {doc['content']}"
            for doc in documents
        ]

    def extract_titles_from_documents(self, documents):
        return [doc['title'] for doc in documents if doc.get('title')]

    def extract_author_from_documents(self, documents):
        return [doc['author'] for doc in documents if doc.get('author')]

    def preprocess_text(self, text):
        stopwords = {"the", "and", "is", "in", "to", "of", "on", "for", "with", "a", "an", "as", "by", "this", "it", "at", "or", "that"}
        translator = str.maketrans('', '', string.punctuation)
        return [word for word in text.lower().translate(translator).split() if word not in stopwords]

    def build_index(self, documents):
        index = defaultdict(lambda: {'doc_ids': [], 'tf': {}})
        doc_lengths = {}
        search_terms = defaultdict(int)

        for doc_id, content in enumerate(documents):
            words = self.preprocess_text(content)
            doc_lengths[doc_id] = len(words)

            for i in range(len(words)):
                word = words[i]
                if doc_id not in index[word]['tf']:
                    index[word]['tf'][doc_id] = 0
                index[word]['tf'][doc_id] += 1
                search_terms[word] += 1

                for j in range(i + 1, min(i + 5, len(words) + 1)):
                    phrase = " ".join(words[i:j])
                    search_terms[phrase] += 1

                index[word]['doc_ids'].append(doc_id)

        return index, doc_lengths, search_terms

    def compute_cosine_similarity(self, query_vector, document_vector):
        dot_product = sum(query_vector.get(term, 0) * document_vector.get(term, 0) for term in query_vector)
        query_magnitude = sqrt(sum(val ** 2 for val in query_vector.values()))
        document_magnitude = sqrt(sum(val ** 2 for val in document_vector.values()))
        if query_magnitude == 0 or document_magnitude == 0:
            return 0.0
        return dot_product / (query_magnitude * document_magnitude)

    def suggest_keywords(self, input_text):
        input_text = input_text.lower()
        suggestions = [term for term in self.search_terms if term.startswith(input_text)]
        return sorted(suggestions, key=lambda x: self.search_terms[x], reverse=True)[:5]

    def search(self, query, index):
        # Preprocess the query text and convert it into a term frequency vector
        query_terms = self.preprocess_text(query)
        query_vector = Counter(query_terms)

        relevant_docs = defaultdict(float)  # Stores cosine similarity for each document

        # Iterate over all terms in the query
        for term in query_terms:
            # Look for partial matches in the index (terms that start with the query term)
            matching_terms = [word for word in index if word.startswith(term)]

            # For each matching term, iterate through the documents in the index
            for matching_term in matching_terms:
                for doc_id, tf in index[matching_term]['tf'].items():
                    # Use the pre-calculated term frequency (TF) for the document
                    document_vector = {matching_term: tf}  # Create a document vector with the pre-calculated TF

                    # Compute cosine similarity between query and document vector
                    similarity = self.compute_cosine_similarity(query_vector, document_vector)
                    relevant_docs[doc_id] += similarity

        # Sort the results by similarity in descending order
        ranked_docs = sorted(relevant_docs.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, _ in ranked_docs:
            doc = self.extracted_documents[doc_id]
            snippet = f"{doc['content'][:180].rsplit(' ', 1)[0]}..." if len(doc['content']) > 100 else doc['content']
            results.append({'title': doc['title'], 'author': doc['author'], 'snippet': snippet, 'file_path': doc['file_name']})

        return results





# Initialize the search engine once when the app starts
search_engine = SearchEngine('Documents')

@app.route('/api/suggestions', methods=['GET'])
def suggestions():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    suggestions = search_engine.suggest_keywords(query)
    return jsonify({"suggestions": suggestions})


@app.route('/api/v2/search/author', methods=['GET'])
def search_author():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.search(query, search_engine.author_index)
    return jsonify({"results": results})

@app.route('/api/v2/search/title', methods=['GET'])
def search_title():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.search(query, search_engine.title_index)
    return jsonify({"results": results})

@app.route('/api/v2/search/fulltext', methods=['GET'])
def search_fulltext():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.search(query, search_engine.content_index)
    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(debug=True)