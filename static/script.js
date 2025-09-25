// Loading messages for better UX
const loadingMessages = [
    "Iniciando análise...",
    "Processando o conteúdo do email...",
    "Consultando a inteligência artificial...",
    "Gerando resposta personalizada...",
    "Finalizando classificação..."
];

let messageIndex = 0;
let loadingInterval;

// DOM Content Loaded Event
document.addEventListener("DOMContentLoaded", () => {
    initializeApp();
});

function initializeApp() {
    // Initialize tabs
    switchTab(localStorage.getItem("activeTab") || "file");
    
    // Setup event listeners
    setupEventListeners();
    
    // Setup drag and drop
    setupDragAndDrop();
    
    console.log("Email Classifier FastAPI - Initialized");
}

function setupEventListeners() {
    // Tab buttons
    document.querySelectorAll(".tab-button").forEach(button => {
        button.addEventListener("click", () => switchTab(button.dataset.tab));
    });
    
    // File input
    const fileInput = document.getElementById("file-input");
    if (fileInput) {
        fileInput.addEventListener("change", handleFileSelect);
    }
    
    // Text input
    const textInput = document.getElementById("text-input");
    if (textInput) {
        textInput.addEventListener("input", handleTextInput);
    }
    
    // Analyze button
    const analyzeButton = document.getElementById("analyze-button");
    if (analyzeButton) {
        analyzeButton.addEventListener("click", analyzeEmail);
    }
    
    // Copy button
    const copyButton = document.getElementById("copy-response");
    if (copyButton) {
        copyButton.addEventListener("click", copyResponse);
    }
}

function setupDragAndDrop() {
    const fileUploadArea = document.getElementById("file-upload-area");
    if (!fileUploadArea) return;
    
    fileUploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        fileUploadArea.classList.add("dragover");
    });
    
    fileUploadArea.addEventListener("dragleave", (e) => {
        e.preventDefault();
        fileUploadArea.classList.remove("dragover");
    });
    
    fileUploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        fileUploadArea.classList.remove("dragover");
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            document.getElementById("file-input").files = files;
            handleFileSelect({ target: { files: files } });
        }
    });
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll(".tab-button").forEach(button => {
        button.classList.remove("active");
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add("active");
    
    // Update tab content
    document.querySelectorAll(".tab-content").forEach(content => {
        content.classList.remove("active");
    });
    document.getElementById(`${tabName}-tab`).classList.add("active");
    
    // Store active tab
    localStorage.setItem("activeTab", tabName);
    
    // Clear previous results and errors
    clearResults();
    updateAnalyzeButton();
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    const fileInputLabel = document.getElementById("file-input-label");
    const fileInfoDiv = document.getElementById("file-info");
    
    if (!file) {
        fileInputLabel.textContent = "Clique aqui ou arraste um arquivo";
        fileInfoDiv.style.display = "none";
        updateAnalyzeButton();
        return;
    }
    
    // Validate file
    const allowedTypes = ["text/plain", "application/pdf"];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    if (!allowedTypes.includes(file.type)) {
        displayError("Tipo de arquivo não suportado. Por favor, envie .txt ou .pdf.");
        return;
    }
    
    if (file.size > maxSize) {
        displayError("Arquivo muito grande. O tamanho máximo permitido é 10MB.");
        return;
    }
    
    // Update UI
    fileInputLabel.textContent = `Arquivo selecionado: ${file.name}`;
    fileInfoDiv.innerHTML = `
        <p><strong>Nome:</strong> ${file.name}</p>
        <p><strong>Tipo:</strong> ${file.type}</p>
        <p><strong>Tamanho:</strong> ${(file.size / (1024 * 1024)).toFixed(2)} MB</p>
    `;
    fileInfoDiv.style.display = "block";
    
    clearError();
    updateAnalyzeButton();
}

function handleTextInput(event) {
    const textInput = event.target;
    const charCount = document.getElementById("char-count");
    const currentLength = textInput.value.length;
    
    charCount.textContent = currentLength.toLocaleString();
    
    // Update char counter color based on limit
    if (currentLength > 45000) {
        charCount.style.color = "#e53e3e";
    } else if (currentLength > 40000) {
        charCount.style.color = "#dd6b20";
    } else {
        charCount.style.color = "#718096";
    }
    
    updateAnalyzeButton();
}

function updateAnalyzeButton() {
    const analyzeButton = document.getElementById("analyze-button");
    const activeTab = localStorage.getItem("activeTab") || "file";
    
    let hasContent = false;
    
    if (activeTab === "file") {
        const fileInput = document.getElementById("file-input");
        hasContent = fileInput.files.length > 0;
    } else {
        const textInput = document.getElementById("text-input");
        hasContent = textInput.value.trim().length > 0;
    }
    
    analyzeButton.disabled = !hasContent;
}

async function analyzeEmail() {
    const activeTab = localStorage.getItem("activeTab") || "file";
    
    clearError();
    clearResults();
    showLoadingScreen();
    
    try {
        const formData = new FormData();
        
        if (activeTab === "file") {
            const fileInput = document.getElementById("file-input");
            const file = fileInput.files[0];
            
            if (!file) {
                throw new Error("Por favor, selecione um arquivo para analisar.");
            }
            
            formData.append("file", file);
        } else {
            const textInput = document.getElementById("text-input");
            const emailContent = textInput.value.trim();
            
            if (!emailContent) {
                throw new Error("Por favor, insira o texto do email para analisar.");
            }
            
            if (emailContent.length > 50000) {
                throw new Error("O texto do email excede o limite de 50.000 caracteres.");
            }
            
            formData.append("email_content", emailContent);
        }
        
        const response = await fetch("/api/email/classify", {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Erro desconhecido na API.");
        }
        
        const data = await response.json();
        displayResults(data);
        
    } catch (error) {
        displayError("Erro ao analisar o email: " + error.message);
    } finally {
        hideLoadingScreen();
    }
}

function displayResults(data) {
    const resultsSection = document.getElementById("results-section");
    const classificationResult = document.getElementById("classification-result");
    const classificationBadge = document.getElementById("classification-badge");
    const classificationText = document.getElementById("classification-text");
    const responseText = document.getElementById("response-text");
    const classificationTime = document.getElementById("classification-time");
    const generationTime = document.getElementById("generation-time");
    const totalTime = document.getElementById("total-time");
    const providerInfo = document.getElementById("provider-info");
    const charCountResult = document.getElementById("char-count-result");
    const analyzedContent = document.getElementById("analyzed-content");
    
    // Show results section
    resultsSection.style.display = "block";
    
    // Update classification
    if (data.classification === "PRODUTIVO") {
        classificationBadge.className = "classification-badge badge-productive";
        classificationResult.className = "result-card productive";
    } else {
        classificationBadge.className = "classification-badge badge-unproductive";
        classificationResult.className = "result-card unproductive";
    }
    
    classificationBadge.textContent = data.classification;
    classificationText.textContent = data.classification_reason;
    responseText.textContent = data.suggested_response;
    
    // Update stats
    classificationTime.textContent = `${data.classification_time}s`;
    generationTime.textContent = `${data.generation_time}s`;
    totalTime.textContent = `${(data.classification_time + data.generation_time).toFixed(2)}s`;
    providerInfo.textContent = `Groq AI (${data.model_used})`;
    charCountResult.textContent = data.char_count.toLocaleString();
    analyzedContent.textContent = data.analyzed_content;
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: "smooth" });
}

function displayError(message) {
    const errorDiv = document.getElementById("error-message");
    errorDiv.textContent = message;
    errorDiv.style.display = "block";
    
    // Scroll to error
    errorDiv.scrollIntoView({ behavior: "smooth" });
}

function clearError() {
    const errorDiv = document.getElementById("error-message");
    errorDiv.style.display = "none";
}

function clearResults() {
    const resultsSection = document.getElementById("results-section");
    resultsSection.style.display = "none";
}

function showLoadingScreen() {
    const loadingOverlay = document.getElementById("loading-overlay");
    const loadingStatus = document.getElementById("loading-status");
    
    loadingOverlay.classList.add("active");
    loadingStatus.textContent = loadingMessages[0];
    messageIndex = 0;
    
    loadingInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % loadingMessages.length;
        loadingStatus.textContent = loadingMessages[messageIndex];
    }, 1500);
}

function hideLoadingScreen() {
    const loadingOverlay = document.getElementById("loading-overlay");
    loadingOverlay.classList.remove("active");
    
    if (loadingInterval) {
        clearInterval(loadingInterval);
    }
}

async function copyResponse() {
    const responseText = document.getElementById("response-text").textContent;
    const copyButton = document.getElementById("copy-response");
    
    try {
        await navigator.clipboard.writeText(responseText);
        
        // Update button text temporarily
        const originalText = copyButton.innerHTML;
        copyButton.innerHTML = '<span>✅</span> Copiado!';
        copyButton.style.background = '#48bb78';
        
        setTimeout(() => {
            copyButton.innerHTML = originalText;
            copyButton.style.background = '#667eea';
        }, 2000);
        
    } catch (err) {
        console.error('Erro ao copiar texto:', err);
        
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = responseText;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        // Update button text temporarily
        const originalText = copyButton.innerHTML;
        copyButton.innerHTML = '<span>✅</span> Copiado!';
        copyButton.style.background = '#48bb78';
        
        setTimeout(() => {
            copyButton.innerHTML = originalText;
            copyButton.style.background = '#667eea';
        }, 2000);
    }
}

// Utility function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Error handling for uncaught errors
window.addEventListener('error', (event) => {
    console.error('Uncaught error:', event.error);
    displayError('Ocorreu um erro inesperado. Por favor, recarregue a página e tente novamente.');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    displayError('Ocorreu um erro de rede. Verifique sua conexão e tente novamente.');
});

console.log("Email Classifier FastAPI - Script loaded successfully");

// Theme Switching Logic

function setupThemeSwitcher() {
    const lightModeBtn = document.getElementById("light-mode-btn");
    const darkModeBtn = document.getElementById("dark-mode-btn");
    const body = document.body;

    function applyTheme(theme) {
        if (theme === "dark") {
            body.classList.add("dark-mode");
            darkModeBtn.classList.add("active");
            lightModeBtn.classList.remove("active");
        } else {
            body.classList.remove("dark-mode");
            lightModeBtn.classList.add("active");
            darkModeBtn.classList.remove("active");
        }
        localStorage.setItem("theme", theme);
    }

    // Apply saved theme on load
    const savedTheme = localStorage.getItem("theme") || "light";
    applyTheme(savedTheme);

    lightModeBtn.addEventListener("click", () => applyTheme("light"));
    darkModeBtn.addEventListener("click", () => applyTheme("dark"));
}

// Call setupThemeSwitcher when the app initializes
const originalInitializeApp = initializeApp;
initializeApp = () => {
    originalInitializeApp();
    setupThemeSwitcher();
};


