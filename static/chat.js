
let conversationHistory = [];

function formatearMensaje(texto) {
    // Convertir markdown básico a HTML
    let formatted = texto;
    
    // Negritas: **texto** o __texto__
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/__(.+?)__/g, '<strong>$1</strong>');
    
    // Cursivas: *texto* o _texto_
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/_(.+?)_/g, '<em>$1</em>');
    
    // Listas con bullets (*, -, •)
    formatted = formatted.replace(/^[\*\-•]\s+(.+)$/gm, '<li>$1</li>');
    
    // Envolver listas consecutivas en <ul>
    formatted = formatted.replace(/(<li>.*<\/li>\s*)+/g, function(match) {
        return '<ul style="margin: 10px 0; padding-left: 20px;">' + match + '</ul>';
    });
    
    // Listas numeradas (1., 2., etc)
    formatted = formatted.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>\s*)+/g, function(match) {
        if (!match.includes('<ul')) {
            return '<ol style="margin: 10px 0; padding-left: 20px;">' + match + '</ol>';
        }
        return match;
    });
    
    // Secciones con encabezados (lineas que terminan en :)
    formatted = formatted.replace(/^([A-ZÁÉÍÓÚ][^:\n]{3,50}):$/gm, '<strong style="display: block; margin-top: 12px; color: #1e3c72;">$1:</strong>');
    
    // Emojis de sección (🏢, 📍, etc seguidos de texto en mayúsculas)
    formatted = formatted.replace(/([📍🏢📞📱⏰📧🎪⚖️])\s+([A-ZÁÉÍÓÚ\s]+)/g, '<div style="margin: 8px 0;"><strong>$1 $2</strong></div>');
    
    // Líneas de separación con guiones
    formatted = formatted.replace(/^[-─]{4,}$/gm, '<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 12px 0;">');
    
    // Saltos de línea
    formatted = formatted.replace(/\n\n/g, '<br><br>');
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Links clickeables
    formatted = formatted.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" style="color: #2a5298; text-decoration: underline;">$1</a>');
    
    return formatted;
}

function addMessage(content, isUser = false, tipo = 'normal') {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    
    let extraClass = '';
    if (tipo === 'sugerencia') {
        extraClass = ' style="opacity: 0.85; font-style: italic; border-left: 3px solid #2a5298; padding-left: 10px;"';
    }
    
    // Formatear el contenido si es del bot
    const formattedContent = isUser ? content : formatearMensaje(content);
    
    messageDiv.innerHTML = `<div class="message-content"${extraClass}>${formattedContent}</div>`;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showTyping() {
    const messagesDiv = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot';
    typingDiv.id = 'typing';
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function removeTyping() {
    const typing = document.getElementById('typing');
    if (typing) typing.remove();
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const message = input.value.trim();

    if (!message) return;

    // Agregar mensaje del usuario
    addMessage(message, true);
    input.value = '';
    sendBtn.disabled = true;

    // Agregar a historial
    conversationHistory.push({
        role: 'user',
        content: message
    });

    // Mostrar indicador de escritura
    showTyping();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                history: conversationHistory
            })
        });

        const data = await response.json();
        removeTyping();

        // Agregar respuesta del bot
        addMessage(data.response, false);

        // Agregar a historial
        conversationHistory.push({
            role: 'assistant',
            content: data.response
        });

        // Mostrar sugerencias si existen
        if (data.sugerencias && data.sugerencias.length > 0) {
            setTimeout(() => {
                data.sugerencias.forEach(sugerencia => {
                    addMessage(`💡 ${sugerencia}`, false, 'sugerencia');
                });
            }, 500);
        }

        // Si necesita ticket, ofrecer crear uno
        if (data.needs_ticket) {
            setTimeout(() => {
                const ticketBtn = `
                    <div class="message bot">
                        <div class="message-content">
                            <button class="btn btn-primary" onclick="openTicketModal()" style="width: 100%; margin-top: 10px;">
                                🎫 Crear Ticket de Soporte
                            </button>
                        </div>
                    </div>
                `;
                document.getElementById('chatMessages').insertAdjacentHTML('beforeend', ticketBtn);
            }, 1000);
        }

    } catch (error) {
        removeTyping();
        addMessage('⚠️ Ocurrió un error. Por favor intenta de nuevo.', false);
        console.error('Error:', error);
    }

    sendBtn.disabled = false;
}

function sendQuickMessage(message) {
    document.getElementById('chatInput').value = message;
    sendMessage();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function openTicketModal() {
    document.getElementById('ticketModal').classList.add('active');
}

function closeTicketModal() {
    document.getElementById('ticketModal').classList.remove('active');
    document.getElementById('ticketForm').reset();
    document.getElementById('successMessage').style.display = 'none';
}

document.getElementById('ticketForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const ticketData = {
        nombre: document.getElementById('ticketNombre').value,
        email: document.getElementById('ticketEmail').value,
        telefono: document.getElementById('ticketTelefono').value,
        asunto: document.getElementById('ticketAsunto').value,
        descripcion: document.getElementById('ticketDescripcion').value
    };

    try {
        const response = await fetch('/api/tickets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ticketData)
        });

        const data = await response.json();

        if (data.success) {
            const successMsg = document.getElementById('successMessage');
            successMsg.textContent = data.message;
            successMsg.style.display = 'block';

            setTimeout(() => {
                closeTicketModal();
                addMessage(`✅ ${data.message}`, false);
            }, 2000);
        }
    } catch (error) {
        alert('Error al crear el ticket. Por favor intenta de nuevo.');
        console.error('Error:', error);
    }
});

// Cerrar modal al hacer clic fuera
document.getElementById('ticketModal').addEventListener('click', (e) => {
    if (e.target.id === 'ticketModal') {
        closeTicketModal();
    }
});
