const API_URL = "https://mindcare-1lns.onrender.com";

// DOM Elements
const memoryInput = document.getElementById('memoryInput');
const queryInput = document.getElementById('queryInput');
const addMemoryBtn = document.getElementById('addMemoryBtn');
const askBtn = document.getElementById('askBtn');
const micMemory = document.getElementById('micMemory');
const micQuery = document.getElementById('micQuery');
const languageSelect = document.getElementById('languageSelect');
const responseArea = document.getElementById('responseArea');
const responseText = document.getElementById('responseText');
const speakResponseBtn = document.getElementById('speakResponseBtn');
const toast = document.getElementById('toast');

// Speech Recognition Setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
} else {
    alert("Web Speech API is not supported in this browser. Voice features will be disabled.");
}

// Helper: Speak Text
function speak(text) {
    if (!text) return;
    window.speechSynthesis.cancel(); // Stop previous
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = languageSelect.value;
    window.speechSynthesis.speak(utterance);
}

// Helper: Listen
function startListening(inputElement, btnElement) {
    if (!recognition) return;

    recognition.lang = languageSelect.value;
    recognition.start();
    btnElement.classList.add('listening');

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        inputElement.value = transcript;
        btnElement.classList.remove('listening');
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        btnElement.classList.remove('listening');
    };

    recognition.onend = () => {
        btnElement.classList.remove('listening');
    };
}

// Event Listeners: Voice
micMemory.addEventListener('click', () => {
    startListening(memoryInput, micMemory);
});

micQuery.addEventListener('click', () => {
    startListening(queryInput, micQuery);
});

speakResponseBtn.addEventListener('click', () => {
    speak(responseText.textContent);
});

// Event Listeners: Add Memory
addMemoryBtn.addEventListener('click', async () => {
    const content = memoryInput.value.trim();
    if (!content) return;

    // Visual feedback
    addMemoryBtn.disabled = true;
    addMemoryBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        const response = await fetch(`${API_URL}/add_memory`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });

        if (response.ok) {
            memoryInput.value = '';
            showToast("Memory saved successfully!");
            // Optional: Speak confirmation
            const msg = languageSelect.value === 'lv-LV' ? 'Atmiņa saglabāta' : 'Memory saved';
            speak(msg);
        } else {
            showToast("Failed to save memory.");
        }
    } catch (error) {
        console.error("Error:", error);
        showToast("Error connecting to server.");
    } finally {
        addMemoryBtn.disabled = false;
        addMemoryBtn.innerHTML = '<i class="fas fa-save"></i> Save Memory';
    }
});

// Event Listeners: Ask Question
askBtn.addEventListener('click', async () => {
    const query = queryInput.value.trim();
    if (!query) return;

    // Visual feedback
    askBtn.disabled = true;
    askBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Thinking...';
    responseArea.classList.add('hidden');

    try {
        const response = await fetch(`${API_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
});

        const data = await response.json();

        if (data.response) {
            responseText.textContent = data.response;
            responseArea.classList.remove('hidden');
            speak(data.response);
        }
    } catch (error) {
        console.error("Error:", error);
        showToast("Error retrieving answer.");
    } finally {
        askBtn.disabled = false;
        askBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Ask MindCare';
    }
});

// Helper: Toast
function showToast(message) {
    toast.textContent = message;
    toast.classList.remove('hidden');
    toast.style.animation = 'none';
    toast.offsetHeight; /* trigger reflow */
    toast.style.animation = 'slideUp 0.3s ease-out';

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}
