# AgentHR Chrome Extension

Build a Chrome extension that integrates with AgentHR to source candidates, parse resumes, and manage recruitment workflows directly from your browser.

## Overview

This extension enables you to:
- Parse resumes from PDF/DOCX files on any website
- Source candidates from LinkedIn and other job boards
- Quick-add candidates to vacancies with one click
- View candidate rankings and match scores inline
- Access AgentHR features from any webpage via context menu

## Prerequisites

- AgentHR API key with appropriate scopes
- Chrome/Edge browser (Chromium-based)
- Basic knowledge of HTML, CSS, JavaScript
- Chrome Developer Mode (for loading unpacked extensions)

## Project Structure

```
agenthr-extension/
├── manifest.json          # Extension manifest
├── popup/
│   ├── popup.html        # Extension popup UI
│   ├── popup.js          # Popup logic
│   └── popup.css         # Popup styles
├── background/
│   └── background.js     # Service worker
├── content/
│   ├── linkedin.js       # LinkedIn integration
│   └── indeed.js         # Indeed integration
├── options/
│   ├── options.html      # Settings page
│   └── options.js        # Settings logic
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

## Setup Guide

### 1. Create Manifest File

Create `manifest.json`:

```json
{
  "manifest_version": 3,
  "name": "AgentHR - AI Recruitment Assistant",
  "version": "1.0.0",
  "description": "Source candidates, parse resumes, and manage recruitment workflows from your browser",
  "permissions": [
    "storage",
    "activeTab",
    "contextMenus",
    "scripting"
  ],
  "host_permissions": [
    "https://api.agenthr.com/*",
    "https://www.linkedin.com/*",
    "https://*.indeed.com/*"
  ],
  "background": {
    "service_worker": "background/background.js"
  },
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "options_page": "options/options.html",
  "content_scripts": [
    {
      "matches": ["https://www.linkedin.com/*"],
      "js": ["content/linkedin.js"],
      "run_at": "document_idle"
    },
    {
      "matches": ["https://*.indeed.com/*"],
      "js": ["content/indeed.js"],
      "run_at": "document_idle"
    }
  ],
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "web_accessible_resources": [
    {
      "resources": ["popup/*"],
      "matches": ["<all_urls>"]
    }
  ]
}
```

### 2. Create Popup UI

Create `popup/popup.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AgentHR</title>
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="container">
    <header>
      <img src="../icons/icon48.png" alt="AgentHR" class="logo">
      <h1>AgentHR</h1>
    </header>

    <div id="auth-section" class="hidden">
      <input
        type="text"
        id="api-key-input"
        placeholder="Enter your AgentHR API Key"
        class="input-field"
      >
      <button id="save-key-btn" class="btn btn-primary">Save API Key</button>
    </div>

    <div id="main-section">
      <div class="quick-actions">
        <button id="parse-resume-btn" class="btn btn-action">
          <span class="icon">📄</span>
          Parse Resume
        </button>
        <button id="add-candidate-btn" class="btn btn-action">
          <span class="icon">➕</span>
          Add Candidate
        </button>
        <button id="check-match-btn" class="btn btn-action">
          <span class="icon">🎯</span>
          Check Match
        </button>
      </div>

      <div id="result-section" class="hidden">
        <div id="loading-spinner" class="spinner hidden"></div>
        <div id="result-content"></div>
      </div>

      <div class="recent-candidates">
        <h2>Recent Candidates</h2>
        <div id="candidates-list"></div>
      </div>
    </div>

    <footer>
      <a href="#" id="settings-link">⚙️ Settings</a>
      <a href="https://agenthr.com/docs" target="_blank">📚 Docs</a>
    </footer>
  </div>

  <script src="popup.js"></script>
</body>
</html>
```

Create `popup/popup.css`:

```css
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  width: 380px;
  min-height: 500px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa;
  color: #2d3748;
}

.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  width: 32px;
  height: 32px;
}

h1 {
  font-size: 20px;
  font-weight: 600;
}

#main-section {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.input-field {
  width: 100%;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 12px;
}

.btn {
  width: 100%;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5568d3;
}

.btn-action {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: white;
  color: #4a5568;
  border: 1px solid #e2e8f0;
  margin-bottom: 8px;
}

.btn-action:hover {
  background: #f7fafc;
  border-color: #cbd5e0;
}

.icon {
  font-size: 18px;
}

.quick-actions {
  margin-bottom: 20px;
}

.result-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.result-card h3 {
  font-size: 16px;
  margin-bottom: 8px;
  color: #2d3748;
}

.result-card p {
  font-size: 13px;
  color: #718096;
  line-height: 1.5;
  margin-bottom: 4px;
}

.skill-tag {
  display: inline-block;
  background: #edf2f7;
  color: #4a5568;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin: 2px;
}

.match-score {
  font-size: 24px;
  font-weight: 700;
  color: #48bb78;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 20px auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.hidden {
  display: none !important;
}

.recent-candidates {
  margin-top: 20px;
}

.recent-candidates h2 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

footer {
  background: white;
  border-top: 1px solid #e2e8f0;
  padding: 12px 16px;
  display: flex;
  justify-content: space-around;
}

footer a {
  color: #718096;
  text-decoration: none;
  font-size: 13px;
}

footer a:hover {
  color: #667eea;
}
```

Create `popup/popup.js`:

```javascript
// API configuration
const API_BASE_URL = 'https://api.agenthr.com';

// DOM elements
let apiKeyInput, saveKeyBtn, authSection, mainSection;
let parseResumeBtn, addCandidateBtn, checkMatchBtn;
let resultSection, loadingSpinner, resultContent;
let candidatesList;

document.addEventListener('DOMContentLoaded', () => {
  // Cache DOM elements
  apiKeyInput = document.getElementById('api-key-input');
  saveKeyBtn = document.getElementById('save-key-btn');
  authSection = document.getElementById('auth-section');
  mainSection = document.getElementById('main-section');
  parseResumeBtn = document.getElementById('parse-resume-btn');
  addCandidateBtn = document.getElementById('add-candidate-btn');
  checkMatchBtn = document.getElementById('check-match-btn');
  resultSection = document.getElementById('result-section');
  loadingSpinner = document.getElementById('loading-spinner');
  resultContent = document.getElementById('result-content');
  candidatesList = document.getElementById('candidates-list');

  // Check for existing API key
  checkAuth();

  // Event listeners
  saveKeyBtn.addEventListener('click', saveApiKey);
  parseResumeBtn.addEventListener('click', handleParseResume);
  addCandidateBtn.addEventListener('click', handleAddCandidate);
  checkMatchBtn.addEventListener('click', handleCheckMatch);
  document.getElementById('settings-link').addEventListener('click', openSettings);

  // Load recent candidates
  loadRecentCandidates();
});

async function checkAuth() {
  const { apiKey } = await chrome.storage.local.get('apiKey');

  if (!apiKey) {
    authSection.classList.remove('hidden');
    mainSection.classList.add('hidden');
  } else {
    authSection.classList.add('hidden');
    mainSection.classList.remove('hidden');
  }
}

async function saveApiKey() {
  const apiKey = apiKeyInput.value.trim();

  if (!apiKey) {
    showError('Please enter an API key');
    return;
  }

  // Validate API key
  try {
    const response = await fetch(`${API_BASE_URL}/api/candidates`, {
      headers: { 'X-API-Key': apiKey }
    });

    if (response.ok) {
      await chrome.storage.local.set({ apiKey });
      authSection.classList.add('hidden');
      mainSection.classList.remove('hidden');
      showSuccess('API key saved successfully');
    } else {
      showError('Invalid API key');
    }
  } catch (error) {
    showError('Failed to validate API key');
  }
}

async function handleParseResume() {
  const [fileHandle] = await window.showOpenFilePicker({
    types: [{
      description: 'Resume files',
      accept: {
        'application/pdf': ['.pdf'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
      }
    }]
  });

  const file = await fileHandle.getFile();
  showLoading(true);

  try {
    const formData = new FormData();
    formData.append('file', file);

    const { apiKey } = await chrome.storage.local.get('apiKey');
    const response = await fetch(`${API_BASE_URL}/api/resumes/upload`, {
      method: 'POST',
      headers: { 'X-API-Key': apiKey },
      body: formData
    });

    if (!response.ok) throw new Error('Failed to parse resume');

    const data = await response.json();
    displayParsedResume(data);
  } catch (error) {
    showError(error.message);
  } finally {
    showLoading(false);
  }
}

async function handleAddCandidate() {
  const { apiKey } = await chrome.storage.local.get('apiKey');

  // Get current tab info for sourcing
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  showLoading(true);

  try {
    let candidateData = {};

    // Extract data based on URL
    if (tab.url.includes('linkedin.com')) {
      candidateData = await extractLinkedInData(tab.id);
    } else {
      // Show manual form
      candidateData = await showManualForm();
    }

    const response = await fetch(`${API_BASE_URL}/api/candidates`, {
      method: 'POST',
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(candidateData)
    });

    if (!response.ok) throw new Error('Failed to add candidate');

    const data = await response.json();
    showSuccess('Candidate added successfully');
    displayCandidateResult(data);

    // Save to recent candidates
    saveToRecent(data);
  } catch (error) {
    showError(error.message);
  } finally {
    showLoading(false);
  }
}

async function handleCheckMatch() {
  const { apiKey } = await chrome.storage.local.get('apiKey');

  // Get vacancies
  const vacanciesResponse = await fetch(
    `${API_BASE_URL}/api/vacancies?limit=10`,
    { headers: { 'X-API-Key': apiKey } }
  );

  const vacanciesData = await vacanciesResponse.json();

  if (!vacanciesData.items || vacanciesData.items.length === 0) {
    showError('No vacancies found');
    return;
  }

  // Show vacancy selector
  const vacancy = await showVacancySelector(vacanciesData.items);
  if (!vacancy) return;

  showLoading(true);

  try {
    // Check current page for candidate info
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    let candidateInfo = {};

    if (tab.url.includes('linkedin.com')) {
      candidateInfo = await extractLinkedInData(tab.id);
    }

    // Get matching candidates
    const response = await fetch(
      `${API_BASE_URL}/api/matching/find-matches?vacancy_id=${vacancy.id}&limit=5`,
      { headers: { 'X-API-Key': apiKey } }
    );

    if (!response.ok) throw new Error('Failed to check matches');

    const data = await response.json();
    displayMatches(data);
  } catch (error) {
    showError(error.message);
  } finally {
    showLoading(false);
  }
}

async function extractLinkedInData(tabId) {
  // Inject content script to extract data
  const results = await chrome.scripting.executeScript({
    target: { tabId },
    func: extractLinkedInProfile
  });

  return results[0].result;
}

// This function runs in the context of the LinkedIn page
function extractLinkedInProfile() {
  return {
    name: document.querySelector('.text-heading-xlarge')?.textContent?.trim() || '',
    email: document.querySelector('.pv-contact-info__contact-link')?.textContent?.trim() || '',
    title: document.querySelector('.text-body-medium')?.textContent?.trim() || '',
    company: document.querySelector('.inline-show-more-text')?.textContent?.trim() || '',
    skills: Array.from(document.querySelectorAll('.pv-skill-category-entity__name'))
      .map(el => el.textContent.trim())
      .slice(0, 10)
  };
}

function displayParsedResume(data) {
  const parsed = data.parsed_data || {};
  resultContent.innerHTML = `
    <div class="result-card">
      <h3>📄 Resume Parsed</h3>
      <p><strong>Name:</strong> ${parsed.name || 'N/A'}</p>
      <p><strong>Email:</strong> ${parsed.email || 'N/A'}</p>
      <p><strong>Phone:</strong> ${parsed.phone_number || 'N/A'}</p>
      <p><strong>Skills:</strong></p>
      <div>
        ${(parsed.skills || []).map(skill =>
          `<span class="skill-tag">${skill}</span>`
        ).join('')}
      </div>
      <button class="btn btn-primary" style="margin-top:12px;" onclick="createCandidateFromResume()">
        Create Candidate
      </button>
    </div>
  `;
  resultSection.classList.remove('hidden');

  // Store parsed data for later use
  window.currentParsedData = data;
}

function displayCandidateResult(data) {
  resultContent.innerHTML = `
    <div class="result-card">
      <h3>✅ Candidate Created</h3>
      <p><strong>Name:</strong> ${data.name || 'N/A'}</p>
      <p><strong>Email:</strong> ${data.email || 'N/A'}</p>
      <p><strong>Stage:</strong> ${data.current_stage || 'Applied'}</p>
    </div>
  `;
  resultSection.classList.remove('hidden');
}

function displayMatches(data) {
  const matches = data.matches || [];
  resultContent.innerHTML = `
    <div class="result-card">
      <h3>🎯 Top Matches</h3>
      ${matches.map(match => `
        <div style="padding: 8px 0; border-top: 1px solid #e2e8f0;">
          <p><strong>${match.name || 'Unknown'}</strong></p>
          <p>Match Score: <span class="match-score">${match.score || 0}%</span></p>
          <p>${match.email || ''}</p>
        </div>
      `).join('')}
    </div>
  `;
  resultSection.classList.remove('hidden');
}

function showLoading(show) {
  if (show) {
    loadingSpinner.classList.remove('hidden');
  } else {
    loadingSpinner.classList.add('hidden');
  }
}

function showError(message) {
  resultContent.innerHTML = `
    <div class="result-card" style="border-left: 4px solid #f56565;">
      <p style="color: #c53030;">❌ ${message}</p>
    </div>
  `;
  resultSection.classList.remove('hidden');
}

function showSuccess(message) {
  resultContent.innerHTML = `
    <div class="result-card" style="border-left: 4px solid #48bb78;">
      <p style="color: #2f855a;">✅ ${message}</p>
    </div>
  `;
  resultSection.classList.remove('hidden');
}

async function showVacancySelector(vacancies) {
  // For simplicity, return first vacancy
  // In a real extension, you'd show a modal with all options
  return vacancies[0];
}

async function showManualForm() {
  // Return a promise that resolves when form is submitted
  return new Promise((resolve) => {
    const name = prompt('Candidate name:');
    if (!name) return null;
    resolve({ name });
  });
}

async function saveToRecent(candidate) {
  const { recentCandidates } = await chrome.storage.local.get('recentCandidates');
  const candidates = recentCandidates || [];
  candidates.unshift(candidate);
  await chrome.storage.local.set({
    recentCandidates: candidates.slice(0, 5) // Keep only 5
  });
  loadRecentCandidates();
}

async function loadRecentCandidates() {
  const { recentCandidates } = await chrome.storage.local.get('recentCandidates');
  const candidates = recentCandidates || [];

  if (candidates.length === 0) {
    candidatesList.innerHTML = '<p style="color: #a0aec0; font-size: 13px;">No recent candidates</p>';
    return;
  }

  candidatesList.innerHTML = candidates.map(c => `
    <div class="result-card" style="padding: 12px; margin-bottom: 8px;">
      <p><strong>${c.name || 'Unknown'}</strong></p>
      <p style="font-size: 12px;">${c.email || ''}</p>
    </div>
  `).join('');
}

function openSettings(e) {
  e.preventDefault();
  chrome.runtime.openOptionsPage();
}

async function createCandidateFromResume() {
  const parsed = window.currentParsedData.parsed_data;
  const { apiKey } = await chrome.storage.local.get('apiKey');

  showLoading(true);

  try {
    const response = await fetch(`${API_BASE_URL}/api/candidates`, {
      method: 'POST',
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: parsed.name,
        email: parsed.email,
        phone: parsed.phone_number,
        skills: parsed.skills,
        source: 'Chrome Extension'
      })
    });

    if (!response.ok) throw new Error('Failed to create candidate');

    const data = await response.json();
    showSuccess('Candidate created from resume');
    saveToRecent(data);
  } catch (error) {
    showError(error.message);
  } finally {
    showLoading(false);
  }
}
```

### 3. Create Background Service Worker

Create `background/background.js`:

```javascript
// Install event - create context menu
chrome.runtime.onInstalled.addListener(() => {
  // Create context menu for resumes
  chrome.contextMenus.create({
    id: 'parse-resume',
    title: 'Parse Resume with AgentHR',
    contexts: ['link', 'selection']
  });

  // Create context menu for candidate sourcing
  chrome.contextMenus.create({
    id: 'add-candidate',
    title: 'Add to AgentHR Candidates',
    contexts: ['page', 'selection']
  });

  console.log('AgentHR extension installed');
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const { apiKey } = await chrome.storage.local.get('apiKey');

  if (!apiKey) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'AgentHR',
      message: 'Please set your API key in the extension popup'
    });
    return;
  }

  if (info.menuItemId === 'parse-resume') {
    await handleParseResume(info, tab, apiKey);
  } else if (info.menuItemId === 'add-candidate') {
    await handleAddCandidate(info, tab, apiKey);
  }
});

async function handleParseResume(info, tab, apiKey) {
  if (info.linkUrl) {
    // Resume link clicked
    chrome.tabs.sendMessage(tab.id, {
      action: 'download-resume',
      url: info.linkUrl
    });
  }
}

async function handleAddCandidate(info, tab, apiKey) {
  // Extract candidate info from page
  chrome.tabs.sendMessage(tab.id, {
    action: 'extract-candidate'
  }, async (response) => {
    if (response && response.data) {
      try {
        const result = await fetch('https://api.agenthr.com/api/candidates', {
          method: 'POST',
          headers: {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(response.data)
        });

        if (result.ok) {
          chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: 'AgentHR',
            message: 'Candidate added successfully'
          });
        }
      } catch (error) {
        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'icons/icon48.png',
          title: 'AgentHR',
          message: 'Failed to add candidate'
        });
      }
    }
  });
}
```

### 4. Create LinkedIn Content Script

Create `content/linkedin.js`:

```javascript
// Inject "Add to AgentHR" button on LinkedIn profiles
function injectAgentHRButton() {
  if (document.querySelector('.agenthr-add-btn')) return; // Already injected

  const profileSection = document.querySelector('.pv-top-card--list-bullet');
  if (!profileSection) return;

  const button = document.createElement('button');
  button.className = 'agenthr-add-btn';
  button.textContent = '➕ Add to AgentHR';
  button.style.cssText = `
    margin-top: 12px;
    padding: 8px 16px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  `;

  button.addEventListener('click', async () => {
    const candidateData = extractLinkedInProfile();
    chrome.runtime.sendMessage({
      action: 'add-candidate',
      data: candidateData
    });
  });

  profileSection.appendChild(button);
}

function extractLinkedInProfile() {
  return {
    name: document.querySelector('.text-heading-xlarge')?.textContent?.trim() || '',
    email: document.querySelector('.pv-contact-info__contact-link')?.textContent?.trim() || '',
    title: document.querySelector('.text-body-medium')?.textContent?.trim() || '',
    company: document.querySelector('.inline-show-more-text')?.textContent?.trim() || '',
    skills: Array.from(document.querySelectorAll('.pv-skill-category-entity__name'))
      .map(el => el.textContent.trim())
      .slice(0, 10),
    source: 'LinkedIn',
    source_url: window.location.href
  };
}

// Run on page load and navigation
injectAgentHRButton();

// LinkedIn is a SPA, so observe for changes
const observer = new MutationObserver(() => {
  injectAgentHRButton();
});

observer.observe(document.body, { childList: true, subtree: true });

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extract-candidate') {
    sendResponse({ data: extractLinkedInProfile() });
  }
});
```

### 5. Create Settings Page

Create `options/options.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AgentHR Settings</title>
  <style>
    body {
      font-family: -apple-system, system-ui, sans-serif;
      max-width: 600px;
      margin: 40px auto;
      padding: 20px;
    }
    h1 { color: #2d3748; }
    .form-group { margin-bottom: 20px; }
    label { display: block; margin-bottom: 8px; font-weight: 500; }
    input, select {
      width: 100%;
      padding: 10px;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
    }
    button {
      padding: 10px 20px;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
    }
    .status { margin-top: 12px; padding: 10px; border-radius: 6px; }
    .success { background: #c6f6d5; color: #22543d; }
    .error { background: #fed7d7; color: #742a2a; }
  </style>
</head>
<body>
  <h1>⚙️ AgentHR Settings</h1>

  <div class="form-group">
    <label>API Key</label>
    <input type="text" id="api-key" placeholder="Enter your AgentHR API key">
  </div>

  <div class="form-group">
    <label>Default Vacancy ID</label>
    <input type="text" id="default-vacancy" placeholder="Optional: Default vacancy for new candidates">
  </div>

  <div class="form-group">
    <label>Auto-parse Resumes</label>
    <select id="auto-parse">
      <option value="true">Yes</option>
      <option value="false">No</option>
    </select>
  </div>

  <button id="save-btn">Save Settings</button>
  <div id="status"></div>

  <script src="options.js"></script>
</body>
</html>
```

Create `options/options.js`:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  document.getElementById('save-btn').addEventListener('click', saveSettings);
});

async function loadSettings() {
  const { apiKey, defaultVacancy, autoParse } = await chrome.storage.local.get([
    'apiKey',
    'defaultVacancy',
    'autoParse'
  ]);

  document.getElementById('api-key').value = apiKey || '';
  document.getElementById('default-vacancy').value = defaultVacancy || '';
  document.getElementById('auto-parse').value = autoParse !== false ? 'true' : 'false';
}

async function saveSettings() {
  const apiKey = document.getElementById('api-key').value.trim();
  const defaultVacancy = document.getElementById('default-vacancy').value.trim();
  const autoParse = document.getElementById('auto-parse').value === 'true';

  await chrome.storage.local.set({
    apiKey,
    defaultVacancy,
    autoParse
  });

  showStatus('Settings saved successfully', 'success');
}

function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${type}`;
  setTimeout(() => status.textContent = '', 3000);
}
```

## Loading the Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select the extension directory
5. The extension should now appear in your browser

## Usage

1. Click the extension icon in the toolbar
2. Enter your AgentHR API key
3. Use quick actions or browse to LinkedIn to source candidates
4. Right-click on resume links to parse them
5. View recent candidates in the popup

## Publishing to Chrome Web Store

1. Create a developer account at [chrome.google.com/webstore/developer](https://chrome.google.com/webstore/developer)
2. Prepare a ZIP file of your extension
3. Fill in the store listing (name, description, screenshots)
4. Upload the ZIP file
5. Pay the $5 registration fee
6. Submit for review

## Resources

- [Chrome Extension Documentation](https://developer.chrome.com/docs/extensions/)
- [AgentHR API Reference](/api/endpoints.md)
- [Manifest V3 Migration Guide](https://developer.chrome.com/docs/extensions/mv3/intro/)
