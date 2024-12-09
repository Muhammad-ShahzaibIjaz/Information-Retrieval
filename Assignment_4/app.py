import os
import string
import math
from docx import Document
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app)



class SearchEngine():

    def __init__(self, folder_path='Documents'):
        self.folder_path = folder_path
        self.documents, self.tf_idf, self.search_terms = self.setup_search_engine(self.folder_path)


    def setup_search_engine(self, folder_path):
        extracted_documents = self.document_extractor(folder_path)
        
        index, doc_lengths, search_terms = self.build_index(extracted_documents)

        idf = self.compute_idf(index, len(extracted_documents))
        tf_idf = self.compute_tf_idf(index, idf, doc_lengths)

        return extracted_documents, tf_idf, search_terms


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
    
    # Preprocess the text by removing stopwords
    def preprocess_text(self, text):
        stopwords = {"the", "and", "is", "in", "to", "of", "on", "for", "with", "a", "an", "as", "by", "this", "it", "at", "or", "that"}
        translator = str.maketrans('', '', string.punctuation)
        return [word for word in text.lower().translate(translator).split() if word not in stopwords]

    # Build index for documents
    def build_index(self, documents):
        index = defaultdict(lambda: {'doc_ids': set(), 'tf': {}})
        doc_lengths = {}
        search_terms = defaultdict(int)

        for doc_id, doc in enumerate(documents):
            total_context = f"{doc['title']} {doc['author']} {doc['content']}".lower()
            words = self.preprocess_text(total_context)
            doc_lengths[doc_id] = len(words)

            for i in range(len(words)):
                word = words[i]
                if doc_id not in index[word]['tf']:
                    index[word]['tf'][doc_id] = 0
                index[word]['tf'][doc_id] += 1
                index[word]['doc_ids'].add(doc_id)
                search_terms[word] += 1

                for j in range(i + 1, min(i + 5, len(words) + 1)):
                    phrase = " ".join(words[i:j])
                    search_terms[phrase] += 1
                    index[phrase]['doc_ids'].add(doc_id)

        return index, doc_lengths, search_terms

    # Compute IDF (Inverse Document Frequency)
    def compute_idf(self, index, num_documents):
        return {word: math.log(num_documents / (1 + len(data['doc_ids']))) for word, data in index.items()}

    # Compute TF-IDF (Term Frequency-Inverse Document Frequency)
    def compute_tf_idf(self, index, idf, doc_lengths):
        return {
            word: {doc_id: (tf / doc_lengths[doc_id]) * idf[word] for doc_id, tf in data['tf'].items()}
            for word, data in index.items()
        }

    
    # Search function for querying documents (with NOLM)
    def search_query(self, query, tf_idf, documents):
        query_keywords = self.preprocess_text(query)
        term_docs = {term: set(tf_idf[term].keys()) for term in query_keywords if term in tf_idf}

        # Combine lists for non-overlapping results
        combined_docs = set()
        for docs in term_docs.values():
            combined_docs.update(docs)
        
        # Rank documents by diversity and score
        ranked_docs = []
        seen_docs = set()
        for doc_id in combined_docs:
            score = sum(tf_idf[term][doc_id] for term in query_keywords if term in tf_idf and doc_id in tf_idf[term])
            if doc_id not in seen_docs:
                ranked_docs.append((doc_id, score))
                seen_docs.add(doc_id)

        ranked_docs.sort(key=lambda x: x[1], reverse=True)

        # Generate results
        result = []
        for doc_id, _ in ranked_docs:
            doc = documents[doc_id]
            snippet = f"{doc['content'][:180].rsplit(' ', 1)[0]}..." if len(doc['content']) > 100 else doc['content']
            result.append({'title': doc['title'], 'author': doc['author'], 'snippet': snippet.replace("Abstract", ""), 'file_path': doc['file_name']})

        return result


    def suggest_keywords(self, input_text):
        input_text = input_text.lower()
        suggestions = [term for term in self.search_terms if term.startswith(input_text)]
        return sorted(suggestions, key=lambda x: self.search_terms[x], reverse=True)[:5]



search_engine = SearchEngine('Documents')

@app.route('/api/v4/suggestions', methods=['GET'])
def suggestions():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    suggestions = search_engine.suggest_keywords(query)
    return jsonify({"suggestions": suggestions})

@app.route('/api/v4/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.search_query(query, search_engine.tf_idf, search_engine.documents)
    return jsonify({"results": results})



if __name__ == "__main__":
    app.run(debug=True)