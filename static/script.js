const chatbotMessages = document.getElementById('chatbot-messages');
const chatbotInput = document.getElementById('chatbot-input');
const chatbotSend = document.getElementById('chatbot-send');
const clientDocsInput = document.getElementById('client-docs');
const uploadButton = document.getElementById('upload-docs');

let clientDocsText = "";
let history = [];

// Fonction pour ajouter un message à l'interface
function addMessage(role, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${role}-message`);
    messageElement.textContent = message;
    chatbotMessages.appendChild(messageElement);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

// Fonction pour ajouter une interaction à l'historique
function addToHistory(question, response) {
    history.push({ question, response });
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
                client_docs_text: clientDocsText,
                user_question: userQuestion,
                history: history
            }),
        });

        const data = await response.json();
        addMessage('bot', data.response);
        addToHistory(userQuestion, data.response);
    }
});

// Téléverser les documents clients
uploadButton.addEventListener('click', async () => {
    const file = clientDocsInput.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = async (event) => {
            clientDocsText = event.target.result;
            alert("Document client téléversé avec succès !");
        };
        reader.readAsText(file);
    }
});