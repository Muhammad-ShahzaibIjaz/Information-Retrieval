import os
import string
import json
from docx import Document
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app)



class SearchEngine:

    def __init__(self, folder_path='Documents', feedback_file='feedback.json'):
        self.folder_path = folder_path
        self.feedback_file = feedback_file
        self.documents, self.content_index, self.title_index, self.search_terms = self.setup_search_engine()
        self.user_feedback = self.load_feedback()

    def setup_search_engine(self):
        extracted_documents = self.document_extractor(self.folder_path)

        extracted_fulltext = self.extract_fullContext_from_documents(extracted_documents)
        extracted_titles = self.extract_titles_from_documents(extracted_documents)

        content_index, search_terms = self.build_binary_index(extracted_fulltext)
        title_index, _ = self.build_binary_index(extracted_titles)

        return extracted_documents, content_index, title_index, search_terms


    def extract_text_from_documents(self, file_path):
        document = Document(file_path)
        doc_data = {'title': "", 'author': "", 'content': ""}

        paragraphs = (p.text.strip() for p in document.paragraphs if p.text.strip())
        for text in paragraphs:
            if not doc_data['title']:
                doc_data['title'] = text
            elif text.startswith("Author:"):
                doc_data['author'] = text[7:].strip()
            else:
                doc_data['content'] += f"{text}"

        return doc_data


    def document_extractor(self, folder_path):
        documents = []

        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)

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


    # Preprocessing function to clean and tokenize text
    def preprocess_text(self, text):
        stopwords = {"the", "and", "is", "in", "to", "of", "on", "for", "with", "a", "an", "as", "by", "this", "it", "at", "or", "that"}
        translator = str.maketrans('', '', string.punctuation)
        return [word for word in text.lower().translate(translator).split() if word not in stopwords]

    # Build binary index for the documents
    def build_binary_index(self, documents):
        index = defaultdict(lambda: {'doc_ids': []})
        search_terms = defaultdict(int)

        for doc_id, content in enumerate(documents):
            words = self.preprocess_text(content.lower())

            # Index individual words
            for word in set(words):  # Use set to avoid duplicates in the same document
                if doc_id not in index[word]['doc_ids']:
                    index[word]['doc_ids'].append(doc_id)
                search_terms[word] += 1

            # Index n-grams (phrases)
            for i in range(len(words)):
                for j in range(i + 1, min(i + 5, len(words) + 1)):  # Create n-grams of length 1 to 4
                    phrase = " ".join(words[i:j])
                    search_terms[phrase] += 1

        return index, search_terms


    # Convert query into a binary vector
    def query_to_binary_vector(self, query, index):
        query_terms = set(self.preprocess_text(query))
        return {term: 1 if term in query_terms else 0 for term in index}

    def dice_similarity(self, query_vector, doc_vector):
        intersection = sum(query_vector[term] * doc_vector.get(term, 0) for term in query_vector)
        total_terms = sum(query_vector.values()) + sum(doc_vector.values())
        return (2 * intersection) / total_terms if total_terms != 0 else 0

    # Function to rank documents based on similarity
    def rank_documents_bim(self, query, index):
        query_vector = self.query_to_binary_vector(query, index)
        ranked_docs = []

        for doc_id in set(doc_id for term in query_vector for doc_id in index[term]['doc_ids']):
            doc_vector = {term: 1 for term in index if doc_id in index[term]['doc_ids']}
            similarity = self.dice_similarity(query_vector, doc_vector)
            if similarity > 0:
                ranked_docs.append((similarity, doc_id))

        ranked_docs.sort(reverse=True, key=lambda x: x[0])
        return [doc_id for similarity, doc_id in ranked_docs]

    # Function to search the documents based on a query
    def search_query_bim(self, documents, index, query):
        ranked_doc_ids = self.rank_documents_bim(query, index)
        results = []

        for rank, doc_id in enumerate(ranked_doc_ids, 1):
            doc = documents[doc_id]
            snippet = f"{doc['content'][:180].rsplit(' ', 1)[0]}..." if len(doc['content']) > 100 else doc['content']
            results.append({
                'doc_id': doc_id,
                'title': doc['title'],
                'author': doc['author'],
                'snippet': snippet.replace("Abstract", ""),
                'file_path': doc['file_name']
            })

        return results


    def suggest_keywords(self, input_text):
        input_text = input_text.lower()
        suggestions = [term for term in self.search_terms if term.startswith(input_text)]
        return sorted(suggestions, key=lambda x: self.search_terms[x], reverse=True)[:5]
    
    def store_feedback(self, doc_id, keyword, relevance):
        self.user_feedback[keyword][doc_id] = relevance

        with open(self.feedback_file, 'w') as f:
            json.dump(self.user_feedback, f)

    def load_feedback(self):
        """ Load feedback from the JSON file if it exists. """
        if os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return defaultdict(lambda: defaultdict(bool))  # Return empty feedback if file is corrupted
        return defaultdict(lambda: defaultdict(bool))

    def get_feedback_for_keyword(self, keyword):
        if keyword in self.user_feedback:
            return [{"doc_id": doc_id, "relevance": relevance} for doc_id, relevance in self.user_feedback[keyword].items()]
        return []

    def evaluate_performance(self, query):
        results = self.search_query_bim(self.documents, self.content_index, query)

        relevant_docs = set()
        retrieved_docs = set()

        feedback = self.get_feedback_for_keyword(query)
        for feedback_item in feedback:
            if feedback_item["relevance"] == "relevant":
                relevant_docs.add(feedback_item["doc_id"])

        for result in results:
            # Convert retrieved doc_id to string for consistency
            retrieved_docs.add(str(result["doc_id"]))

        precision = len(relevant_docs & retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0
        recall = len(relevant_docs & retrieved_docs) / len(relevant_docs) if relevant_docs else 0
        f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {'precision': precision, 'recall': recall, 'f1-score': f1_score}




search_engine = SearchEngine('Documents', 'feedback.json')

@app.route('/api/suggestions', methods=['GET'])
def suggestions():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    suggestions = search_engine.suggest_keywords(query)
    return jsonify({"suggestions": suggestions})


@app.route('/api/v3/search/title', methods=['GET'])
def search_author():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.search_query_bim(search_engine.documents, search_engine.title_index, query)
    return jsonify({"results": results})

@app.route('/api/v3/search/content', methods=['GET'])
def search_content():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.search_query_bim(search_engine.documents, search_engine.content_index, query)
    return jsonify({"results": results})

@app.route('/api/v3/feedback', methods=['POST'])
def store_keyword_feedback():
    try:
        data = request.get_json()
        doc_id = data.get('doc_id')
        keyword = data.get('keyword')
        relevance = data.get('relevance')
        
        if doc_id is None or keyword is None or relevance is None:
            return jsonify({"error": "doc_id, keyword, and relevance are required"}), 400
        
        search_engine.store_feedback(doc_id, keyword, relevance)
        return jsonify({"message": "Feedback successfully stored"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/v3/evaluate', methods=['GET'])
def evaluate_model():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.evaluate_performance(query)
    return jsonify({"results": results})



if __name__ == "__main__":
    app.run(debug=True)