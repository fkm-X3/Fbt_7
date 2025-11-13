const chatBox = document.getElementById('chat-box');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');

        async function sendMessage() {
            const message = messageInput.value.trim();

            if (!message) {
                alert('Please enter a message.');
                return;
            }

            appendMessage('user', message);
            messageInput.value = '';

            try {
                const response = await fetch('http://localhost:11434/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model: 'mistral',
                        prompt: message,
                        stream: false
                    }),
                });

                const data = await response.json();
                if (!response.ok) throw new Error('API request failed');

                appendMessage('assistant', data.response);
            } catch (error) {
                appendMessage('assistant', `⚠️ Error: ${error.message}`);
            }
        }

        function appendMessage(role, text) {
            const msg = document.createElement('div');
            msg.className = `message ${role}`;
            msg.textContent = text;
            chatBox.appendChild(msg);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });