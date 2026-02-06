/**
 * Novio AI Assistant - Chat JavaScript
 * Sidebar + Chat layout with green fintech theme
 */

document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');
    const sendButton = document.getElementById('sendButton');

    // Sidebar elements
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
    const sidebarExpandTab = document.getElementById('sidebarExpandTab');
    const newChatBtn = document.getElementById('newChatBtn');

    // AI Icon SVG
    const aiIconSVG = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a4 4 0 0 1 4 4v1a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/>
            <path d="M12 11v2"/>
            <path d="M8 15h8"/>
            <circle cx="9" cy="18" r="1"/>
            <circle cx="15" cy="18" r="1"/>
            <path d="M6 11a6 6 0 0 0 12 0"/>
            <path d="M12 22v-3"/>
            <path d="M7 22h10"/>
            <path d="M5 6a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2"/>
            <path d="M19 6a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2"/>
        </svg>
    `;

    // User Icon SVG
    const userIconSVG = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
            <path d="M12 14l-3 3"/>
            <path d="M12 14l3 3"/>
            <circle cx="12" cy="7" r="1" fill="currentColor"/>
        </svg>
    `;

    // Welcome message HTML (used by New Chat)
    const welcomeMessageHTML = `
        <div class="message assistant-message welcome-message">
            <div class="message-avatar">
                <div class="avatar-icon">
                    ${aiIconSVG}
                </div>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <p>Hello! I'm your <strong>Novio AI Assistant</strong>. I can help you with:</p>
                    <ul>
                        <li>FD-backed credit cards</li>
                        <li>Account creation and KYC</li>
                        <li>Card features and benefits</li>
                        <li>Payments and transactions</li>
                        <li>General support queries</li>
                    </ul>
                    <p>How can I assist you today?</p>
                </div>
            </div>
        </div>
    `;

    // ===== SIDEBAR LOGIC =====

    function isMobile() {
        return window.innerWidth < 768;
    }

    // Mobile: open drawer
    function openSidebar() {
        sidebar.classList.add('open');
        sidebar.classList.remove('collapsed');
        sidebarOverlay.classList.add('active');
    }

    // Mobile: close drawer
    function closeSidebar() {
        sidebar.classList.remove('open');
        sidebarOverlay.classList.remove('active');
    }

    // Desktop: collapse sidebar
    function collapseSidebar() {
        sidebar.classList.add('collapsed');
    }

    // Desktop: expand sidebar
    function expandSidebar() {
        sidebar.classList.remove('collapsed');
    }

    // Hamburger button (mobile only)
    hamburgerBtn.addEventListener('click', openSidebar);

    // Close button (mobile drawer X)
    sidebarCloseBtn.addEventListener('click', closeSidebar);

    // Collapse arrow button (in sidebar footer, desktop)
    sidebarCollapseBtn.addEventListener('click', collapseSidebar);

    // Expand tab (visible when collapsed, desktop)
    sidebarExpandTab.addEventListener('click', expandSidebar);

    // Overlay click closes sidebar
    sidebarOverlay.addEventListener('click', closeSidebar);

    // Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (isMobile()) {
                closeSidebar();
            } else {
                collapseSidebar();
            }
        }
    });

    // Auto-close mobile drawer when resizing to desktop
    window.addEventListener('resize', function() {
        if (!isMobile()) {
            closeSidebar();
        }
    });

    // ===== NEW CHAT =====

    newChatBtn.addEventListener('click', function() {
        chatMessages.innerHTML = welcomeMessageHTML;
        if (isMobile()) {
            closeSidebar();
        }
        messageInput.focus();
    });

    // ===== TEXTAREA AUTO-RESIZE =====

    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });

    // Handle Enter key (Shift+Enter for new line)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // ===== QUICK ACTION BUTTONS & KEYWORD CHIPS =====

    document.querySelectorAll('.quick-action-btn, .keyword-chip').forEach(btn => {
        btn.addEventListener('click', function() {
            const query = this.getAttribute('data-query');
            if (query) {
                messageInput.value = query;
                chatForm.dispatchEvent(new Event('submit'));
                // Auto-close sidebar on mobile
                if (isMobile()) {
                    closeSidebar();
                }
            }
        });
    });

    // ===== FORM SUBMISSION =====

    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const message = messageInput.value.trim();
        if (!message) return;

        // Disable input while processing
        setInputState(false);

        // Add user message to chat
        addMessage(message, 'user');

        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Show typing indicator
        showTypingIndicator(true);

        // Scroll to bottom
        scrollToBottom();

        try {
            // Send message to API
            const response = await sendMessage(message);

            // Hide typing indicator
            showTypingIndicator(false);

            // Add assistant response
            addMessage(response.answer, 'assistant');

        } catch (error) {
            console.error('Error:', error);
            showTypingIndicator(false);
            addMessage(
                'I apologize, but I encountered an error. Please try again or contact support if the issue persists.',
                'assistant'
            );
        }

        // Re-enable input
        setInputState(true);
        messageInput.focus();

        // Scroll to bottom
        scrollToBottom();
    });

    /**
     * Send message to the chat API
     */
    async function sendMessage(message) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Add a message to the chat
     */
    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';

        const avatarIcon = document.createElement('div');
        avatarIcon.className = 'avatar-icon';

        if (type === 'user') {
            avatarIcon.innerHTML = userIconSVG;
        } else {
            avatarIcon.innerHTML = aiIconSVG;
        }

        avatarDiv.appendChild(avatarIcon);

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';

        // Format message content
        if (type === 'assistant') {
            bubbleDiv.innerHTML = formatMessage(content);
        } else {
            bubbleDiv.textContent = content;
        }

        contentDiv.appendChild(bubbleDiv);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        chatMessages.appendChild(messageDiv);
    }

    /**
     * Format message content (handle markdown-like formatting)
     */
    function formatMessage(content) {
        // Escape HTML first
        let formatted = escapeHtml(content);

        // Convert line breaks to <br>
        formatted = formatted.replace(/\n/g, '<br>');

        // Convert markdown-style bold **text**
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Convert markdown-style italic *text*
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Convert markdown-style code `code`
        formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');

        // Convert URLs to links
        formatted = formatted.replace(
            /(https?:\/\/[^\s<]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );

        // Convert bullet points
        formatted = formatted.replace(/^[-•]\s+(.*)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

        return formatted;
    }

    /**
     * Escape HTML entities
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show or hide typing indicator
     */
    function showTypingIndicator(show) {
        if (show) {
            typingIndicator.classList.add('visible');
        } else {
            typingIndicator.classList.remove('visible');
        }
    }

    /**
     * Enable or disable input
     */
    function setInputState(enabled) {
        messageInput.disabled = !enabled;
        sendButton.disabled = !enabled;
    }

    /**
     * Scroll chat to bottom
     */
    function scrollToBottom() {
        const chatContainer = document.querySelector('.chat-container');
        setTimeout(() => {
            chatContainer.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    }

    // Focus input on page load
    messageInput.focus();
});
