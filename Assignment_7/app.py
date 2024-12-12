import os
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def extract_text_from_documents(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text
    except FileNotFoundError:
        print(f"Error: The file at {file_path} does not exist.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def document_extractor(folder_path):
    documents = []

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        file_name_without_extension = os.path.splitext(file_name)[0]

        if not (os.path.isfile(file_path) and file_name.endswith('.txt')):
            continue

        text = extract_text_from_documents(file_path)

        if text is not None:
            doc_data = {
                'file_name': file_name,
                'title' : file_name_without_extension,
                'text': text
            }

            documents.append(doc_data)

    return documents

# Function to create links based on document titles
def create_hypertext_links(documents):
    links = defaultdict(list)

    for source_doc in documents:
        source_title = source_doc['title']
        for target_doc in documents:
            if source_doc == target_doc:
                continue

            target_title = target_doc['title']
            if target_title.lower() in source_doc['text'].lower():  # Check if target title is in source text
                if target_title not in links[source_title]:
                    links[source_title].append(target_title)

    return links


@app.route('/api/v7/content', methods=['GET'])
def get_documents():
    documents = document_extractor("Documents")
    links = create_hypertext_links(documents)
    return jsonify({"results": documents, "links": links})

if __name__ == "__main__":
    app.run(debug=True)

    