import os
import string
import math
from docx import Document
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# The purpose of making this class is to 
# maintains the state across requests and avoids re-initializing the documents and indexes.
class SearchEngine:
    def __init__(self, folder_path='Documents'):
        self.folder_path = folder_path
        self.extracted_documents = []
        self.doc_lengths = {}
        self.content_idf = {}
        self.content_tf_idf = {}
        self.title_idf = {}
        self.title_tf_idf = {}
        self.author_idf = {}
        self.author_tf_idf = {}
        self.search_terms = defaultdict(int)
        self.setup_search_engine()

    # Function to extract doc_data from specific docx file
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
                doc_data['content'] += f"{text}"
        content = doc_data['title'] + doc_data['author'] + doc_data['content'].replace("Abstract", "").strip()
        doc_data['content'] = content

        return doc_data

    # Function to extract all content from the Document folder
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
    
    # After successfully, extracting text from docx file, this function will separate the title content. 
    def extract_titles_from_documents(self, documents):
        return [doc['title'] for doc in documents if doc.get('title')]

    # Similarly, this function will separate the author content.
    def extract_author_from_documents(self, documents):
        return [doc['author'] for doc in documents if doc.get('author')]

    # Function to clear the stopword like "A Question" => "Question"
    def preprocess_text(self, text):
        stopwords = {"the", "and", "is", "in", "to", "of", "on", "for", "with", "a", "an", "as", "by", "this", "it", "at", "or", "that"}
        translator = str.maketrans('', '', string.punctuation)
        return [word for word in text.lower().translate(translator).split() if word not in stopwords]

    # Function which build inverted index where each unique term maps to the documents that contain it,
    # and it also calculate TF (Term Frequency) for each document, return search terms for suggestion purpose.
    def build_index(self, documents):
        index = defaultdict(lambda: {'doc_ids': [], 'tf': {}})
        doc_lengths = {}
        search_terms = defaultdict(int)

        for doc_id, content in enumerate(documents):
            words = self.preprocess_text(content.lower())
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

    def compute_idf(self, index, num_documents):
        return {word: math.log(num_documents / (1 + len(data['doc_ids']))) for word, data in index.items()}

    def compute_tf_idf(self, index, idf, doc_lengths):
        return {
            word: {doc_id: (tf / doc_lengths[doc_id]) * idf[word] for doc_id, tf in data['tf'].items()}
            for word, data in index.items()
        }

    # Function to return the result according to the user query
    def search_query(self, query, tf_idf, idf, doc_lengths, documents):
        query_keywords = self.preprocess_text(query)
        query_tf_idf = {keyword: idf.get(keyword, 0) for keyword in query_keywords}

        matched_docs = defaultdict(float)
        
        for word, query_score in query_tf_idf.items():
            for term in tf_idf:
                if word in term.lower():
                    for doc_id, doc_score in tf_idf[term].items():
                        matched_docs[doc_id] += query_score * doc_score

        ranked_docs = sorted(matched_docs.items(), key=lambda x: x[1], reverse=True)

        result = []
        for doc_id, _ in ranked_docs:
            doc = documents[doc_id]
            snippet = f"{doc['content'][:180].rsplit(' ', 1)[0]}..." if len(doc['content']) > 100 else doc['content']
            result.append({'title': doc['title'], 'author': doc['author'], 'snippet': snippet, 'file_path': doc['file_name']})

        return result

    # Function that will suggest user keyword for searching for their ease.
    def get_suggestions(self, query, search_terms, max_suggestions=5):
        query = query.lower()
        matches = (term for term in search_terms if term.startswith(query))
        sorted_matches = sorted(matches, key=lambda term: -search_terms[term])
        return sorted_matches[:max_suggestions]

    # Initialize Function
    def setup_search_engine(self):
        self.extracted_documents = self.document_extractor()

        extracted_fulltext = self.extract_fullContext_from_documents(self.extracted_documents)
        extracted_titles = self.extract_titles_from_documents(self.extracted_documents)
        extracted_authors = self.extract_author_from_documents(self.extracted_documents)

        content_index, doc_lengths, search_terms = self.build_index(extracted_fulltext)
        title_index, _, _ = self.build_index(extracted_titles)
        author_index, _, _ = self.build_index(extracted_authors)

        num_documents = len(self.extracted_documents)

        self.content_idf = self.compute_idf(content_index, num_documents)
        self.author_idf = self.compute_idf(author_index, num_documents)
        self.title_idf = self.compute_idf(title_index, num_documents)

        self.content_tf_idf = self.compute_tf_idf(content_index, self.content_idf, doc_lengths)
        self.title_tf_idf = self.compute_tf_idf(title_index, self.title_idf, doc_lengths)
        self.author_tf_idf = self.compute_tf_idf(author_index, self.author_idf, doc_lengths)
        self.search_terms = search_terms


search_engine = SearchEngine(folder_path='Documents')


@app.route('/suggestions', methods=['GET'])
def suggestions():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    suggestions = search_engine.get_suggestions(query, search_engine.search_terms, max_suggestions=6)
    return jsonify({"suggestions": suggestions})


@app.route('/api/v1/search/fulltext', methods=['GET'])
def search_fulltext():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.search_query(query, search_engine.content_tf_idf, search_engine.content_idf, search_engine.doc_lengths, search_engine.extracted_documents)
    return jsonify({"results": results})


@app.route('/api/v1/search/author', methods=['GET'])
def search_author():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.search_query(query, search_engine.author_tf_idf, search_engine.author_idf, search_engine.doc_lengths, search_engine.extracted_documents)
    return jsonify({"results": results})


@app.route('/api/v1/search/title', methods=['GET'])
def search_title():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.search_query(query, search_engine.title_tf_idf, search_engine.title_idf, search_engine.doc_lengths, search_engine.extracted_documents)
    return jsonify({"results": results})


if __name__ == '__main__':
    app.run(debug=True)
