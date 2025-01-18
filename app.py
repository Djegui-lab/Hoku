from flask import Flask, request, jsonify, send_from_directory
import json
import os
import re
import logging
from datetime import datetime
from google.generativeai import GenerativeModel, configure
from googleapiclient.discovery import build
from google.oauth2 import service_account
import boto3
from concurrent.futures import ThreadPoolExecutor

# Configuration de la journalisation
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Initialisation de Gemini
configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)

# Initialisation des services Google
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
]
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
google_credentials = json.loads(SERVICE_ACCOUNT_JSON)
credentials = service_account.Credentials.from_service_account_info(google_credentials, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=credentials)
docs_service = build("docs", "v1", credentials=credentials)

# Charger les documents des compagnies d'assurance
def load_docs_text(folder_ids):
    docs_text = ""
    for folder_id in folder_ids:
        files = list_files_in_folder(folder_id, drive_service)
        if files:
            for file in files:
                if file["mimeType"] == "application/vnd.google-apps.document":
                    doc_text = get_google_doc_text(file["id"], docs_service)
                    docs_text += f"\n\n---\n\n{doc_text}"
    return docs_text

# Lister les fichiers dans un dossier Google Drive
def list_files_in_folder(folder_id, drive_service):
    try:
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name, mimeType)"
        ).execute()
        return results.get("files", [])
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des fichiers : {e}")
        return []

# Extraire le texte d'un document Google Docs
def get_google_doc_text(doc_id, docs_service):
    try:
        document = docs_service.documents().get(documentId=doc_id).execute()
        text_content = ""
        for element in document.get("body", {}).get("content", []):
            if "paragraph" in element:
                for text_run in element.get("paragraph", {}).get("elements", []):
                    if "textRun" in text_run:
                        text_content += text_run["textRun"]["content"]
        return text_content.strip()
    except Exception as e:
        return f"Erreur lors de la lecture du document Google Docs : {e}"

# Fonction pour interroger Gemini
def query_gemini_with_history(docs_text, client_docs_text, user_question, history, model="gemini-2.0-flash-exp"):
    try:
        history_str = "\n".join([f"Q: {h['question']}\nR: {h['response']}" for h in history])
        prompt = f"""
**System message**

---

### **Rôle :**  
Je suis 🤖 **Assurbot** 🤖, une assistance intelligente pour courtiers en assurance, entraînée et créée par **DJEGUI WAGUE**. Mon rôle est d'aider les courtiers à déterminer si un client est éligible aux conditions de souscription des produits d'assurance, en proposant les meilleures garanties, formules et options adaptées aux besoins du client.  

---

### **Historique des conversations :**  
{history_str}  

### **Documents des compagnies d'assurance :**  
{docs_text}  

### **Documents clients :**  
{client_docs_text}  

**Question :** {user_question}  
"""
        model = GenerativeModel(model_name=model)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Erreur lors de l'interrogation de Gemini : {e}"

# Endpoint pour interroger le chatbot
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_question = data.get("user_question", "")
    client_docs_text = data.get("client_docs_text", "")
    history = data.get("history", [])

    folder_ids = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "").split(",")
    folder_ids = [folder_id.strip() for folder_id in folder_ids if folder_id.strip()]
    docs_text = load_docs_text(folder_ids)

    response = query_gemini_with_history(docs_text, client_docs_text, user_question, history)
    return jsonify({"response": response})

# Route pour servir le fichier HTML (frontend)
@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

# Route pour servir les fichiers statiques (CSS, JS)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


