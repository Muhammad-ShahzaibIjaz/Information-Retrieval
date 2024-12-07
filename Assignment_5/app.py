import os
import string
import difflib
import networkx as nx
from nltk.stem import PorterStemmer
from docx import Document
from flask import Flask, request, jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

stemmer = PorterStemmer()


class SearchEngine():

    def __init__(self, folder_path='Documents'):
        self.folder_path = folder_path
        self.documents, self.graph = self.setup_search_engine(self.folder_path)
        self.search_terms = self.build_term_repository(self.documents)


    def setup_search_engine(self, folder_path):
        extracted_documents = self.document_extractor(folder_path)
        graph = self.build_proximity_graph(extracted_documents)

        return extracted_documents, graph


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
        words = text.lower().translate(translator).split()
        return [stemmer.stem(word) for word in words if word not in stopwords]

    # Build proximity graph
    def build_proximity_graph(self, documents):
        graph = nx.Graph()
        
        for doc_id, doc in enumerate(documents):
            title_nodes = self.preprocess_text(doc['title'])
            author_nodes = self.preprocess_text(doc['author'])
            content_nodes = self.preprocess_text(doc['content'])
            all_nodes = set(title_nodes + author_nodes + content_nodes)

            # Add document and related nodes to the graph
            graph.add_node(doc_id, type="document", title=doc['title'])
            for node in all_nodes:
                graph.add_node(node, type="term")
                graph.add_edge(doc_id, node)
        
        return graph
    
    # Fuzzy matching for related terms
    def get_related_terms(self, query_term, graph, threshold=0.6):
        all_terms = [node for node, attrs in graph.nodes(data=True) if attrs.get('type') == 'term']
        related_terms = difflib.get_close_matches(query_term, all_terms, n=5, cutoff=threshold)
        return related_terms
    
    # Proximal Nodes Model Search
    def proximal_nodes_search(self, query, graph, documents):
        query_nodes = self.preprocess_text(query)
        proximal_nodes = set()

        for node in query_nodes:
            # Add exact matches
            if node in graph:
                proximal_nodes.update(nx.neighbors(graph, node))
            
            # Add fuzzy matches
            related_terms = self.get_related_terms(node, graph)
            for related_node in related_terms:
                if related_node in graph:
                    proximal_nodes.update(nx.neighbors(graph, related_node))

        # Fetch documents connected to the proximal nodes
        connected_docs = {node for node in proximal_nodes if graph.nodes[node].get('type') == 'document'}
        results = []

        for doc_id in connected_docs:
            doc = documents[doc_id]
            snippet = f"{doc['content'][:180].rsplit(' ', 1)[0]}..." if len(doc['content']) > 100 else doc['content']
            results.append({'title': doc['title'], 'author': doc['author'], 'snippet': snippet.replace("Abstract", ""), 'file_path': doc['file_name']})

        return results


    def build_term_repository(self, documents):
        term_frequencies = {}
        for doc in documents:
            terms = self.preprocess_text(doc['title']) + self.preprocess_text(doc['author']) + self.preprocess_text(doc['content'])
            for term in terms:
                term_frequencies[term] = term_frequencies.get(term, 0) + 1
        return term_frequencies

    def suggest_keywords(self, input_text):
        input_text = input_text.lower()
        all_terms = self.search_terms.keys()
        
        # Fuzzy match and prefix match
        prefix_matches = [term for term in all_terms if term.startswith(input_text)]
        fuzzy_matches = difflib.get_close_matches(input_text, all_terms, n=5, cutoff=0.6)
        
        # Combine results, prioritize prefix matches
        suggestions = list(set(prefix_matches + fuzzy_matches))
        suggestions.sort(key=lambda term: self.search_terms[term], reverse=True)  # Rank by frequency
        
        return suggestions[:5]



search_engine = SearchEngine('Documents')

@app.route('/api/v5/suggestions', methods=['GET'])
def suggestions():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    suggestions = search_engine.suggest_keywords(query)
    return jsonify({"suggestions": suggestions})

@app.route('/api/v5/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_engine.proximal_nodes_search(query, search_engine.graph, search_engine.documents)
    return jsonify({"results": results})



if __name__ == "__main__":
    app.run(debug=True)