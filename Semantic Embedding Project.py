#Note: Cosine similarity cutoff is relatively arbitrary. It will read the top ten abstacts above 0.5 similarity.
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import xml.etree.ElementTree as ET

xml_file_path = "pubmed24n1219.xml"
json_file_path = "json_database.json"
client = OpenAI()
MODEL = "text-embedding-3-small"
user_input = "Does FLX increase neuronal numbers?"

with open(xml_file_path, encoding='utf-8'):
    
    def generate_text_embedding(text, model=MODEL):
        text = text.replace("\n", " ")
        return client.embeddings.create(input = [text], model = model).data[0].embedding

    def user(user_input):
        user_embedding = generate_text_embedding(user_input)
        user_embedding = np.array(user_embedding).reshape(1,-1)
        return user_embedding
    
    def list_from_database(xml_file_path):
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        abstracts_embeddings = {}
        for abstract in root.findall('.//PubmedArticle')[0:100]:  
            if abstract.find('.//AbstractText') is not None:
                title = abstract.find('.//Title').text
                abstract_text = abstract.find('.//AbstractText').text
                abstract_embedding = generate_text_embedding(abstract_text)
                abstracts_embeddings[abstract_text] = abstract_embedding
        return abstracts_embeddings

    def create_database(xml_file_path, json_file_path):
        with open ("json_database.json", "w") as json_file:
            abstracts_embeddings = list_from_database(xml_file_path)
            json.dump(abstracts_embeddings, json_file)

    #create_database(xml_file_path, json_file_path) #Run this one time
    
def load_database(json_file_path):
    with open(json_file_path, "r") as json_file:
        data = json.load(json_file)
    for key in data:
        data[key] = np.array(data[key])
    return data

def find_most_similar_abstract(user_input, json_file_path):
    user_embedding = np.array(generate_text_embedding(user_input)).reshape(1, -1)
    abstracts_embeddings = load_database(json_file_path)
    similarity_scores = []
    for abstract_text, abstract_embedding in abstracts_embeddings.items():
        abstract_embedding = np.array(abstract_embedding).reshape(1, -1)  
        similarity = cosine_similarity(user_embedding, abstract_embedding)[0][0]
        if similarity > 0.5:
            similarity_scores.append((abstract_text, similarity))
    similarity_scores.sort(key=lambda x: x[1], reverse=True)
    top_similar_abstracts = similarity_scores[:10]
    response = "\n\n".join([abstract[0] for abstract in top_similar_abstracts])
    return response

def generate_answer_based_on_abstract(user_input, json_file_path):
    abstract = find_most_similar_abstract(user_input, json_file_path)
    if abstract:
        messages = [
            {"role": "system", "content": "You are a knowledgeable assistant who provides information based on scientific abstracts."},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": abstract}  
        ]
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return completion.choices[0].message.content
    else:
        return "I'm sorry, but I couldn't find a relevant abstract for your question."

answer = generate_answer_based_on_abstract(user_input, json_file_path)
print(answer)



