from flask import Flask, request, jsonify
import json
import os
import re
import logging
from datetime import datetime
from google.generativeai import GenerativeModel, configure

# Configuration de la journalisation
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Initialisation de Gemini
configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)

# Fonction pour interroger Gemini
def query_gemini_with_history(docs_text, client_docs_text, user_question, history, model="gemini-2.0-flash-exp"):
    try:
        # Convertir l'historique en une chaîne de caractères
        history_str = "\n".join([f"Q: {h['question']}\nR: {h['response']}" for h in history])
        
        # Construire le prompt
        prompt = f"""
**System message**

---

### **Rôle :**  
Je suis 🤖 **Assurbot** 🤖, une assistance intelligente pour courtiers en assurance, entraînée et créée par **DJEGUI WAGUE**. Mon rôle est d'aider les courtiers à déterminer si un client est éligible aux conditions de souscription des produits d'assurance, en proposant les meilleures garanties, formules et options adaptées aux besoins du client.  

**Objectifs :**  
- Aider les courtiers à identifier les produits d'assurance qui acceptent ou refusent un client.  
- **Ne jamais estimer les primes d'assurance.**  
- Utiliser les fiches produits des courtiers grossistes (comme APRIL, Maxance, Zéphir, etc.) et analyser les documents clients (carte grise, permis de conduire, relevé d'information, etc.).  

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
    docs_text = data.get("docs_text", "")
    client_docs_text = data.get("client_docs_text", "")
    user_question = data.get("user_question", "")
    history = data.get("history", [])

    response = query_gemini_with_history(docs_text, client_docs_text, user_question, history)
    return jsonify({"response": response})

# Route pour servir le fichier HTML (frontend)
@app.route('/')
def serve_index():
    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chatbot Assurance</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                margin: 0;
                padding: 0;
            }
            #chatbot-widget {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 350px;
                height: 500px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                display: flex;
                flex-direction: column;
            }
            #chatbot-header {
                background: #0078d7;
                color: white;
                padding: 15px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                text-align: center;
                font-size: 18px;
                font-weight: bold;
            }
            #chatbot-messages {
                flex: 1;
                padding: 10px;
                overflow-y: auto;
                background: #f9f9f9;
            }
            #chatbot-input-container {
                display: flex;
                padding: 10px;
                border-top: 1px solid #ddd;
            }
            #chatbot-input {
                flex: 1;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-right: 10px;
            }
            #chatbot-send {
                padding: 10px 20px;
                background: #0078d7;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            .message {
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 5px;
                max-width: 80%;
            }
            .user-message {
                background: #0078d7;
                color: white;
                align-self: flex-end;
            }
            .bot-message {
                background: #e1e1e1;
                color: black;
                align-self: flex-start;
            }
        </style>
    </head>
    <body>
        <div id="chatbot-widget">
            <div id="chatbot-header">🤖 Assurbot</div>
            <div id="chatbot-messages"></div>
            <div id="chatbot-input-container">
                <input type="text" id="chatbot-input" placeholder="Posez votre question...">
                <button id="chatbot-send">Envoyer</button>
            </div>
        </div>

        <script>
            const chatbotMessages = document.getElementById('chatbot-messages');
            const chatbotInput = document.getElementById('chatbot-input');
            const chatbotSend = document.getElementById('chatbot-send');

            // Fonction pour ajouter un message à l'interface
            function addMessage(role, message) {
                const messageElement = document.createElement('div');
                messageElement.classList.add('message', `${role}-message`);
                messageElement.textContent = message;
                chatbotMessages.appendChild(messageElement);
                chatbotMessages.scrollTop = chatbotMessages.scrollHeight; // Faire défiler vers le bas
            }

            // Envoyer une question à l'API
            chatbotSend.addEventListener('click', async () => {
                const userQuestion = chatbotInput.value.trim();
                if (userQuestion) {
                    addMessage('user', userQuestion);
                    chatbotInput.value = '';

                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            docs_text: "",  // Remplacez par les documents des compagnies d'assurance
                            client_docs_text: "",  // Remplacez par les documents clients
                            user_question: userQuestion,
                            history: []  // Remplacez par l'historique des conversations
                        }),
                    });

                    const data = await response.json();
                    addMessage('bot', data.response);
                }
            });
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True)
