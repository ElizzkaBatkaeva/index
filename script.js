document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const loginForm = document.getElementById('login-form');
    const chatInterface = document.getElementById('chat-interface');
    const usernameInput = document.getElementById('username-input');
    const loginBtn = document.getElementById('login-btn');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const messagesContainer = document.getElementById('messages-container');
    const usersCount = document.getElementById('users-count');
    const usersList = document.getElementById('users-list');
    
    let currentUsername = '';
    
    // Функция для добавления сообщения в чат
    function addMessage(message, isOwn = false, isSystem = false) {
        const messageDiv = document.createElement('div');
        
        if (isSystem) {
            messageDiv.className = 'system-message';
            messageDiv.textContent = `${message.username} ${message.message} (${message.timestamp})`;
        } else {
            messageDiv.className = isOwn ? 'message own' : 'message other';
            
            const messageHeader = document.createElement('div');
            messageHeader.className = 'message-header';
            messageHeader.innerHTML = `<span>${message.username}</span><span>${message.timestamp}</span>`;
            
            const messageText = document.createElement('div');
            messageText.className = 'message-text';
            messageText.textContent = message.message;
            
            messageDiv.appendChild(messageHeader);
            messageDiv.appendChild(messageText);
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Функция для обновления списка пользователей
    function updateUsersList(users) {
        usersCount.textContent = users.length;
        usersList.innerHTML = '';
        
        users.forEach(user => {
            const userItem = document.createElement('span');
            userItem.className = 'user-item';
            userItem.textContent = user;
            usersList.appendChild(userItem);
        });
    }
    
    // Обработчик входа в чат
    loginBtn.addEventListener('click', function() {
        const username = usernameInput.value.trim();
        
        if (username) {
            currentUsername = username;
            socket.emit('join', { username: username });
            
            loginForm.style.display = 'none';
            chatInterface.style.display = 'flex';
            messageInput.focus();
        }
    });
    
    // Обработчик отправки сообщения
    function sendMessage() {
        const message = messageInput.value.trim();
        
        if (message) {
            socket.emit('message', {
                username: currentUsername,
                message: message
            });
            
            messageInput.value = '';
        }
    }
    
    sendBtn.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Обработчики событий от сервера
    socket.on('message', function(data) {
        const isOwn = data.username === currentUsername;
        addMessage(data, isOwn);
    });
    
    socket.on('user_joined', function(data) {
        addMessage({
            username: data.username,
            message: 'присоединился к чату',
            timestamp: data.timestamp
        }, false, true);
    });
    
    socket.on('user_left', function(data) {
        addMessage({
            username: data.username,
            message: 'покинул чат',
            timestamp: data.timestamp
        }, false, true);
    });
    
    socket.on('users_update', function(data) {
        updateUsersList(data.users);
    });
});