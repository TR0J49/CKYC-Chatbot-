// ====== STATE ======
let currentLang = 'en';
let currentUserType = null;
let wrongCount = 0;
let selectedRatingValue = 0;
let selectedRatingText = '';
let translations = {};

// ====== INIT ======
document.addEventListener('DOMContentLoaded', () => {
    showScreen('languageScreen');
});

// ====== SCREEN MANAGEMENT ======
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById(screenId);
    if (screen) {
        screen.classList.add('active');
    }

    // Show/hide chat input
    const chatInput = document.getElementById('chatInputArea');
    if (screenId === 'chatScreen') {
        chatInput.style.display = 'block';
    } else {
        chatInput.style.display = 'none';
    }

    // Scroll to top of chat body
    document.getElementById('chatBody').scrollTop = 0;
}

// ====== LANGUAGE SELECTION ======
async function selectLanguage(lang) {
    currentLang = lang;

    await fetch('/api/set-language', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: lang })
    });

    // Load translations
    const res = await fetch(`/api/translations?lang=${lang}`);
    translations = await res.json();

    applyTranslations();
    showScreen('userTypeScreen');
}

function applyTranslations() {
    const map = {
        'headerTitle': 'welcome_title',
        'userTypePrompt': 'select_user_type',
        'reLabel': 'registered_entity',
        'clientLabel': 'client',
        'menuPrompt': 'select_option',
        'statusLabel': 'check_status',
        'queryLabel': 'raise_query',
        'chatLabel': 'ask_question',
        'regStatusLabel': 'status_registration',
        'walletLabel': 'wallet_inquiry',
        'mismatchLabel': 'mismatch_details',
        'regPrompt': 'enter_reg_number',
        'walletPrompt': 'enter_re_number',
        'mismatchPrompt': 'enter_ckyc_number',
        'feedbackTitle': 'feedback_prompt',
        'thankYouMsg': 'thank_you',
        'menuBtnLabel': currentLang === 'hi' ? 'मेनू' : 'Menu',
        'endChatLabel': 'end_chat',
        'backLabel1': 'back',
        'backLabel2': 'back',
        'backLabel3': 'back',
        'backLabel4': 'back',
        'rVeryBad': 'very_bad',
        'rBad': 'bad',
        'rGood': 'good',
        'rVeryGood': 'very_good',
        'rExcellent': 'excellent',
    };

    for (const [elemId, transKey] of Object.entries(map)) {
        const el = document.getElementById(elemId);
        if (el && translations[transKey]) {
            el.textContent = translations[transKey];
        }
    }

    // Placeholders
    const chatInputEl = document.getElementById('chatInput');
    if (chatInputEl && translations['type_question']) {
        chatInputEl.placeholder = translations['type_question'];
    }

    // Status text
    const statusText = document.getElementById('statusText');
    if (statusText) {
        statusText.textContent = currentLang === 'hi' ? 'ऑनलाइन' : 'Online';
    }
}

// ====== USER TYPE SELECTION ======
async function selectUserType(type) {
    currentUserType = type;

    await fetch('/api/set-user-type', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_type: type })
    });

    showScreen('menuScreen');
}

// ====== MAIN MENU OPTIONS ======
function selectOption(option) {
    switch (option) {
        case 'status':
            showScreen('apiScreen');
            break;
        case 'query':
            raiseQuery();
            break;
        case 'chat':
            startChat();
            break;
    }
}

function goToMenu() {
    wrongCount = 0;
    showScreen('menuScreen');
}

// ====== RAISE QUERY/COMPLAINT ======
function raiseQuery() {
    const msg = translations['raise_query_redirect'] || 'You will be redirected to the Web Portal to raise your Query/Complaint.';
    addBotMessage(msg);
    showScreen('chatScreen');

    // Simulate redirect delay
    setTimeout(() => {
        addBotMessage(currentLang === 'hi'
            ? 'वेब पोर्टल पर रीडायरेक्ट हो रहा है...'
            : 'Redirecting to the Web Portal...');
        // In production, window.open('https://portal.ckycindia.in/complaint', '_blank');
    }, 1500);
}

// ====== CHAT ======
function startChat() {
    wrongCount = 0;
    document.getElementById('messagesContainer').innerHTML = '';
    showScreen('chatScreen');

    const greeting = translations['hello_response'] || 'Hello! How can I help you today?';
    addBotMessage(greeting);
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    addUserMessage(message);
    input.value = '';

    // Show typing indicator
    showTyping();

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await res.json();

        // Remove typing indicator
        hideTyping();

        addBotMessage(data.response);

        if (data.show_redirect) {
            wrongCount = 0;
            // After redirect message, show feedback option
            setTimeout(() => {
                endChat();
            }, 2000);
        }
    } catch (err) {
        hideTyping();
        addBotMessage(currentLang === 'hi'
            ? 'कुछ गलत हो गया। कृपया पुनः प्रयास करें।'
            : 'Something went wrong. Please try again.');
    }
}

function addBotMessage(text) {
    const container = document.getElementById('messagesContainer');
    const div = document.createElement('div');
    div.className = 'message bot';
    div.innerHTML = `
        <div class="avatar"><i class="fas fa-robot"></i></div>
        <div class="bubble">${escapeHtml(text)}</div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function addUserMessage(text) {
    const container = document.getElementById('messagesContainer');
    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = `
        <div class="avatar"><i class="fas fa-user"></i></div>
        <div class="bubble">${escapeHtml(text)}</div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function showTyping() {
    const container = document.getElementById('messagesContainer');
    const div = document.createElement('div');
    div.className = 'message bot';
    div.id = 'typingIndicator';
    div.innerHTML = `
        <div class="avatar"><i class="fas fa-robot"></i></div>
        <div class="bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function hideTyping() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
}

function scrollToBottom() {
    const body = document.getElementById('chatBody');
    body.scrollTop = body.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// ====== API INTEGRATION ======
function selectApiOption(option) {
    switch (option) {
        case 'registration':
            showScreen('registrationScreen');
            document.getElementById('regResult').style.display = 'none';
            document.getElementById('regNumberInput').value = '';
            break;
        case 'wallet':
            showScreen('walletScreen');
            document.getElementById('walletResult').style.display = 'none';
            document.getElementById('walletOptions').style.display = 'none';
            document.getElementById('reNumberInput').value = '';
            break;
        case 'mismatch':
            showScreen('mismatchScreen');
            document.getElementById('mismatchResult').style.display = 'none';
            document.getElementById('ckycNumberInput').value = '';
            break;
    }
}

async function checkRegistrationStatus() {
    const input = document.getElementById('regNumberInput');
    const regNumber = input.value.trim();
    if (!regNumber) return;

    const resultDiv = document.getElementById('regResult');
    resultDiv.style.display = 'block';
    resultDiv.textContent = currentLang === 'hi' ? 'जाँच हो रही है...' : 'Checking...';
    resultDiv.className = 'result-box';

    try {
        const res = await fetch('/api/check-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reg_number: regNumber })
        });
        const data = await res.json();
        resultDiv.textContent = data.response || data.error;
        if (data.error) resultDiv.className = 'result-box error';
    } catch {
        resultDiv.textContent = 'Error occurred';
        resultDiv.className = 'result-box error';
    }
}

function showWalletOptions() {
    const reNumber = document.getElementById('reNumberInput').value.trim();
    if (!reNumber) return;

    // Validate numeric
    if (!/^\d+$/.test(reNumber)) {
        alert(currentLang === 'hi' ? 'कृपया केवल संख्यात्मक मान दर्ज करें' : 'Please enter numeric value only');
        return;
    }

    document.getElementById('walletOptions').style.display = 'flex';
}

async function walletInquiry(option) {
    const reNumber = document.getElementById('reNumberInput').value.trim();
    const resultDiv = document.getElementById('walletResult');
    resultDiv.style.display = 'block';
    resultDiv.textContent = currentLang === 'hi' ? 'जाँच हो रही है...' : 'Checking...';
    resultDiv.className = 'result-box';

    try {
        const res = await fetch('/api/wallet-inquiry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ re_number: reNumber, option })
        });
        const data = await res.json();
        resultDiv.textContent = data.response || data.error;
        if (data.error) resultDiv.className = 'result-box error';
    } catch {
        resultDiv.textContent = 'Error occurred';
        resultDiv.className = 'result-box error';
    }
}

async function checkMismatch() {
    const input = document.getElementById('ckycNumberInput');
    const ckycNumber = input.value.trim();
    if (!ckycNumber) return;

    const resultDiv = document.getElementById('mismatchResult');
    resultDiv.style.display = 'block';
    resultDiv.textContent = currentLang === 'hi' ? 'जाँच हो रही है...' : 'Checking...';
    resultDiv.className = 'result-box';

    try {
        const res = await fetch('/api/mismatch-check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ckyc_number: ckycNumber })
        });
        const data = await res.json();

        if (res.ok) {
            resultDiv.textContent = data.response;
        } else {
            resultDiv.textContent = data.error;
            resultDiv.className = 'result-box error';
        }
    } catch {
        resultDiv.textContent = 'Error occurred';
        resultDiv.className = 'result-box error';
    }
}

// ====== FEEDBACK ======
async function endChat() {
    // Show feedback screen
    showScreen('feedbackScreen');
    document.getElementById('feedbackTextArea').style.display = 'none';
    document.getElementById('feedbackResponse').style.display = 'none';
    selectedRatingValue = 0;
    selectedRatingText = '';

    // Remove selected state from all rating buttons
    document.querySelectorAll('.rating-btn').forEach(btn => btn.classList.remove('selected'));
}

function selectRating(value, text) {
    selectedRatingValue = value;
    selectedRatingText = text;

    // Highlight selected
    document.querySelectorAll('.rating-btn').forEach(btn => btn.classList.remove('selected'));
    event.currentTarget.classList.add('selected');

    // Show text area for bad/very bad ratings
    if (value <= 2) {
        document.getElementById('feedbackTextArea').style.display = 'block';
    } else {
        // Directly submit for good ratings
        submitFeedback();
    }
}

async function submitFeedback() {
    if (selectedRatingValue === 0) return;

    const feedbackText = document.getElementById('feedbackText')
        ? document.getElementById('feedbackText').value.trim()
        : '';

    try {
        const res = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rating: selectedRatingText,
                rating_value: selectedRatingValue,
                feedback_text: feedbackText
            })
        });
        const data = await res.json();

        // Show response
        const responseDiv = document.getElementById('feedbackResponse');
        responseDiv.textContent = data.response;
        responseDiv.style.display = 'block';

        // Hide rating buttons and textarea
        document.querySelector('.rating-buttons').style.display = 'none';
        document.getElementById('feedbackTextArea').style.display = 'none';

        // Show submitted message
        const submitted = translations['feedback_submitted'] || 'Submitted successfully.';
        const feedbackSubtitle = document.getElementById('feedbackSubtitle');
        if (feedbackSubtitle) feedbackSubtitle.textContent = submitted;

        // Navigate to thank you after delay
        setTimeout(() => {
            showScreen('thankYouScreen');
        }, 3000);
    } catch {
        // Handle error silently
    }
}

// ====== RESET CHAT ======
async function resetChat() {
    wrongCount = 0;

    await fetch('/api/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });

    // Reset feedback UI
    const ratingBtns = document.querySelector('.rating-buttons');
    if (ratingBtns) ratingBtns.style.display = 'flex';

    document.querySelectorAll('.rating-btn').forEach(btn => btn.classList.remove('selected'));

    const feedbackText = document.getElementById('feedbackText');
    if (feedbackText) feedbackText.value = '';

    // Reset messages
    document.getElementById('messagesContainer').innerHTML = '';

    showScreen('languageScreen');
}

// ====== TOGGLE CHAT (widget mode) ======
function toggleChat() {
    const container = document.getElementById('chatContainer');
    const btn = document.getElementById('chatWidgetBtn');

    if (container.style.display === 'none') {
        container.style.display = 'flex';
        btn.style.display = 'none';
        document.getElementById('unreadBadge').style.display = 'none';
    } else {
        container.style.display = 'none';
        btn.style.display = 'flex';
    }
}
