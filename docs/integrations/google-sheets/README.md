# AgentHR Google Sheets Integration

Sync candidates, vacancies, and recruitment data between AgentHR and Google Sheets for reporting, analysis, and collaboration.

## Overview

This integration enables you to:
- Export candidates to Google Sheets with one click
- Keep sheets in sync with AgentHR data (two-way sync)
- Build custom reports and dashboards
- Collaborate with stakeholders who prefer spreadsheets
- Use Google Apps Script for custom automation

## Prerequisites

- AgentHR API key with appropriate scopes
- Google Cloud project with Google Sheets API enabled
- Google service account or OAuth credentials
- Basic knowledge of Google Apps Script

## Setup Guide

### Option 1: Google Apps Script (Recommended)

This method uses OAuth and doesn't require a service account.

#### Step 1: Create a New Google Sheet

1. Go to [sheets.google.com](https://sheets.google.com) and create a new sheet
2. Name it "AgentHR Candidates"
3. Create these sheets (tabs):
   - **Candidates** - Main candidate data
   - **Vacancies** - Job openings
   - **Activities** - Recent activities

#### Step 2: Open Apps Script Editor

1. In your Google Sheet, go to **Extensions** > **Apps Script**
2. Delete any existing code
3. Rename the project to "AgentHR Integration"

#### Step 3: Add the Integration Code

Create a file named `AgentHR.gs`:

```javascript
// AgentHR API Configuration
const AGENTHR_API_URL = 'https://api.agenthr.com';
const AGENTHR_API_KEY = 'your_api_key_here'; // Or use PropertiesService

// Cache for rate limiting
const CACHE_PREFIX = 'agenthr_cache_';

/**
 * Fetch candidates from AgentHR
 * @param {number} limit - Maximum number of candidates to fetch
 * @param {number} skip - Number of candidates to skip (pagination)
 * @return {Array} Array of candidate objects
 */
function fetchCandidates(limit = 100, skip = 0) {
  const cacheKey = `${CACHE_PREFIX}candidates_${limit}_${skip}`;
  const cached = CacheService.getScriptCache().get(cacheKey);

  if (cached) {
    return JSON.parse(cached);
  }

  const options = {
    method: 'GET',
    headers: {
      'X-API-Key': AGENTHR_API_KEY,
      'Content-Type': 'application/json'
    },
    muteHttpExceptions: true
  };

  const url = `${AGENTHR_API_URL}/api/candidates?limit=${limit}&skip=${skip}`;
  const response = UrlFetchApp.fetch(url, options);

  if (response.getResponseCode() !== 200) {
    throw new Error(`Failed to fetch candidates: ${response.getContentText()}`);
  }

  const data = JSON.parse(response.getContentText());
  CacheService.getScriptCache().put(cacheKey, JSON.stringify(data.items), 300); // 5 min cache

  return data.items || [];
}

/**
 * Fetch vacancies from AgentHR
 * @return {Array} Array of vacancy objects
 */
function fetchVacancies() {
  const cacheKey = `${CACHE_PREFIX}vacancies`;
  const cached = CacheService.getScriptCache().get(cacheKey);

  if (cached) {
    return JSON.parse(cached);
  }

  const options = {
    method: 'GET',
    headers: {
      'X-API-Key': AGENTHR_API_KEY,
      'Content-Type': 'application/json'
    },
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(`${AGENTHR_API_URL}/api/vacancies`, options);

  if (response.getResponseCode() !== 200) {
    throw new Error(`Failed to fetch vacancies: ${response.getContentText()}`);
  }

  const data = JSON.parse(response.getContentText());
  CacheService.getScriptCache().put(cacheKey, JSON.stringify(data.items), 300);

  return data.items || [];
}

/**
 * Fetch analytics from AgentHR
 * @param {string} startDate - Start date (ISO format)
 * @param {string} endDate - End date (ISO format)
 * @return {Object} Analytics data
 */
function fetchAnalytics(startDate, endDate) {
  const options = {
    method: 'GET',
    headers: {
      'X-API-Key': AGENTHR_API_KEY,
      'Content-Type': 'application/json'
    },
    muteHttpExceptions: true
  };

  const url = `${AGENTHR_API_URL}/api/analytics/key-metrics?start_date=${startDate}&end_date=${endDate}`;
  const response = UrlFetchApp.fetch(url, options);

  if (response.getResponseCode() !== 200) {
    throw new Error(`Failed to fetch analytics: ${response.getContentText()}`);
  }

  return JSON.parse(response.getContentText());
}

/**
 * Write candidates to the Candidates sheet
 */
function syncCandidatesToSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Candidates') || ss.insertSheet('Candidates');

  // Clear existing data
  sheet.clear();
  sheet.setFrozenRows(1);

  // Add headers
  const headers = [
    'ID',
    'Name',
    'Email',
    'Phone',
    'Current Stage',
    'Vacancy',
    'Source',
    'Created At',
    'Tags',
    'Skills'
  ];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');

  // Fetch candidates
  const candidates = fetchCandidates(500);

  if (candidates.length === 0) {
    Logger.log('No candidates found');
    return;
  }

  // Prepare data rows
  const rows = candidates.map(c => [
    c.id || '',
    c.name || '',
    c.email || '',
    c.phone || '',
    c.current_stage || '',
    c.vacancy_title || '',
    c.source || '',
    c.created_at ? new Date(c.created_at).toLocaleDateString() : '',
    (c.tags || []).join(', '),
    (c.skills || []).join(', ')
  ]);

  // Write data
  if (rows.length > 0) {
    sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
  }

  // Auto-resize columns
  sheet.autoResizeColumns(1, headers.length);

  Logger.log(`Synced ${candidates.length} candidates to sheet`);
  return candidates.length;
}

/**
 * Write vacancies to the Vacancies sheet
 */
function syncVacanciesToSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Vacancies') || ss.insertSheet('Vacancies');

  sheet.clear();
  sheet.setFrozenRows(1);

  const headers = [
    'ID',
    'Title',
    'Location',
    'Status',
    'Work Format',
    'Employment Type',
    'Min Experience',
    'Salary Min',
    'Salary Max',
    'Created At',
    'Required Skills'
  ];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');

  const vacancies = fetchVacancies();

  if (vacancies.length === 0) {
    Logger.log('No vacancies found');
    return;
  }

  const rows = vacancies.map(v => [
    v.id || '',
    v.title || '',
    v.location || '',
    v.status || '',
    v.work_format || '',
    v.employment_type || '',
    v.min_experience_years || '',
    v.salary_min || '',
    v.salary_max || '',
    v.created_at ? new Date(v.created_at).toLocaleDateString() : '',
    (v.required_skills || []).join(', ')
  ]);

  if (rows.length > 0) {
    sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
  }

  sheet.autoResizeColumns(1, headers.length);
  Logger.log(`Synced ${vacancies.length} vacancies to sheet`);
  return vacancies.length;
}

/**
 * Create a dashboard with key metrics
 */
function createDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName('Dashboard');

  if (!sheet) {
    sheet = ss.insertSheet('Dashboard');
  } else {
    sheet.clear();
  }

  // Get analytics for last 30 days
  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  const analytics = fetchAnalytics(startDate, endDate);
  const candidates = fetchCandidates(1000);
  const vacancies = fetchVacancies();

  // Calculate metrics
  const totalCandidates = candidates.length;
  const totalVacancies = vacancies.length;
  const hiredCount = candidates.filter(c => c.current_stage === 'Hired').length;

  // Stage distribution
  const stageCounts = {};
  candidates.forEach(c => {
    const stage = c.current_stage || 'Unknown';
    stageCounts[stage] = (stageCounts[stage] || 0) + 1;
  });

  // Build dashboard
  sheet.getRange('A1').setValue('AgentHR Recruitment Dashboard');
  sheet.getRange('A1').setFontWeight('bold').setFontSize(18);

  // Summary cards
  sheet.getRange('A3').setValue('Total Candidates');
  sheet.getRange('B3').setValue(totalCandidates);
  sheet.getRange('A3').setFontWeight('bold');

  sheet.getRange('A4').setValue('Total Vacancies');
  sheet.getRange('B4').setValue(totalVacancies);
  sheet.getRange('A4').setFontWeight('bold');

  sheet.getRange('A5').setValue('Hired (Last 30 days)');
  sheet.getRange('B5').setValue(hiredCount);
  sheet.getRange('A5').setFontWeight('bold');

  // Stage distribution
  sheet.getRange('A7').setValue('Stage Distribution');
  sheet.getRange('A7').setFontWeight('bold');

  const stageRows = Object.entries(stageCounts).map(([stage, count]) => [stage, count]);
  if (stageRows.length > 0) {
    sheet.getRange('A8', 1, stageRows.length, 2).setValues(stageRows);
  }

  // Create a chart
  if (stageRows.length > 0) {
    const chart = sheet.newChart()
      .setChartType(Charts.ChartType.PIE)
      .addRange(sheet.getRange('A8', 1, stageRows.length, 2))
      .setPosition(10, 4, 0, 0)
      .build();

    sheet.addChart(chart);
  }

  sheet.autoResizeColumns(1, 3);
  Logger.log('Dashboard created');
}

/**
 * Add a new candidate to AgentHR from sheet
 * @param {Object} candidateData - Candidate data
 */
function addCandidate(candidateData) {
  const options = {
    method: 'POST',
    headers: {
      'X-API-Key': AGENTHR_API_KEY,
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify(candidateData),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(`${AGENTHR_API_URL}/api/candidates`, options);

  if (response.getResponseCode() !== 201) {
    throw new Error(`Failed to add candidate: ${response.getContentText()}`);
  }

  return JSON.parse(response.getContentText());
}

/**
 * Update candidate stage
 * @param {string} candidateId - Candidate ID
 * @param {string} newStage - New stage name
 * @param {string} vacancyId - Vacancy ID
 */
function updateCandidateStage(candidateId, newStage, vacancyId) {
  const options = {
    method: 'PUT',
    headers: {
      'X-API-Key': AGENTHR_API_KEY,
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify({
      stage: newStage,
      vacancy_id: vacancyId
    }),
    muteHttpExceptions: true
  };

  const url = `${AGENTHR_API_URL}/api/candidates/${candidateId}/stage`;
  const response = UrlFetchApp.fetch(url, options);

  if (response.getResponseCode() !== 200) {
    throw new Error(`Failed to update stage: ${response.getContentText()}`);
  }

  return JSON.parse(response.getContentText());
}

/**
 * Create custom menu
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('AgentHR')
    .addItem('Sync Candidates', 'syncCandidatesToSheet')
    .addItem('Sync Vacancies', 'syncVacanciesToSheet')
    .addItem('Create Dashboard', 'createDashboard')
    .addSeparator()
    .addItem('Clear Cache', 'clearCache')
    .addItem('Settings', 'showSettings')
    .addToUi();
}

/**
 * Clear API cache
 */
function clearCache() {
  const cache = CacheService.getScriptCache();
  cache.removeAll(cache.getAllKeys().filter(k => k.startsWith(CACHE_PREFIX)));
  SpreadsheetApp.getUi().alert('Cache cleared');
}

/**
 * Show settings dialog
 */
function showSettings() {
  const html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; }
      label { display: block; margin-bottom: 5px; font-weight: bold; }
      input, select { width: 100%; margin-bottom: 15px; padding: 8px; }
      button { padding: 10px 20px; background: #4285f4; color: white; border: none; cursor: pointer; }
    </style>
    <h3>AgentHR Settings</h3>
    <label>API Key:</label>
    <input type="text" id="apiKey" value="${AGENTHR_API_KEY}">
    <button onclick="saveSettings()">Save</button>
    <script>
      function saveSettings() {
        const apiKey = document.getElementById('apiKey').value;
        google.script.run.withSuccessHandler(() => {
          google.script.host.close();
        }).saveApiKeyToProperties(apiKey);
      }
    </script>
  `)
    .setWidth(300)
    .setHeight(200);

  SpreadsheetApp.getUi().showModalDialog(html, 'AgentHR Settings');
}

/**
 * Save API key to script properties
 */
function saveApiKeyToProperties(apiKey) {
  PropertiesService.getScriptProperties().setProperty('AGENTHR_API_KEY', apiKey);
}

/**
 * Get API key from properties or use default
 */
function getApiKey() {
  return PropertiesService.getScriptProperties().getProperty('AGENTHR_API_KEY') || AGENTHR_API_KEY;
}
```

#### Step 4: Save and Run

1. Save the script (Ctrl+S or Cmd+S)
2. Update the `AGENTHR_API_KEY` constant or use the Settings menu
3. Run `syncCandidatesToSheet` from the function dropdown
4. Grant permissions when prompted
5. Open your Google Sheet - you should see a new **AgentHR** menu

#### Step 5: Set Up Automatic Sync

Create a time-based trigger:

1. In Apps Script, go to **Triggers** (clock icon)
2. Click **Add Trigger**
3. Choose:
   - Function: `syncCandidatesToSheet`
   - Event source: **Time-driven**
   - Type: **Hour timer**
   - Every: **1 hour**
4. Click **Save**

Your sheet will now sync with AgentHR every hour.

---

### Option 2: Python with Service Account

For more advanced automation, use Python with a service account.

#### Step 1: Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project
3. Enable the **Google Sheets API**

#### Step 2: Create a Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Grant it **Editor** role on your Google Sheet
4. Create a JSON key and download it

#### Step 3: Install Dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

#### Step 4: Create the Sync Script

Create `sheets_sync.py`:

```python
import os
import httplib2
import httpx
from google.oauth2 import service_account
from googleapiclient import discovery
from datetime import datetime

# Configuration
AGENTHR_API_KEY = os.environ["AGENTHR_API_KEY"]
AGENTHR_API_URL = "https://api.agenthr.com"
SPREADSHEET_ID = "your_spreadsheet_id"
SERVICE_ACCOUNT_FILE = "service_account.json"

# Google Sheets scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    """Authenticate and return Google Sheets service"""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = discovery.build('sheets', 'v4', credentials=credentials)
    return service

def fetch_candidates():
    """Fetch candidates from AgentHR"""
    async def _fetch():
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AGENTHR_API_URL}/api/candidates",
                headers={"X-API-Key": AGENTHR_API_KEY},
                params={"limit": 500}
            )
            response.raise_for_status()
            return response.json()

    import asyncio
    return asyncio.run(_fetch())

def sync_candidates_to_sheet():
    """Sync candidates to Google Sheet"""
    service = get_sheets_service()
    data = fetch_candidates()
    candidates = data.get("items", [])

    # Prepare data rows
    rows = [["ID", "Name", "Email", "Phone", "Stage", "Vacancy", "Created"]]

    for c in candidates:
        rows.append([
            c.get("id", ""),
            c.get("name", ""),
            c.get("email", ""),
            c.get("phone", ""),
            c.get("current_stage", ""),
            c.get("vacancy_title", ""),
            c.get("created_at", "")
        ])

    # Clear and update sheet
    range_name = "Candidates!A1:G500"
    body = {"values": rows}

    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=body
    ).execute()

    print(f"Synced {len(candidates)} candidates")

def add_candidate_from_sheet(row_data):
    """Add a candidate to AgentHR from sheet data"""
    async def _add():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENTHR_API_URL}/api/candidates",
                headers={
                    "X-API-Key": AGENTHR_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "name": row_data[1],
                    "email": row_data[2],
                    "phone": row_data[3] if len(row_data) > 3 else None,
                    "source": "Google Sheets"
                }
            )
            response.raise_for_status()
            return response.json()

    import asyncio
    return asyncio.run(_add())

if __name__ == "__main__":
    sync_candidates_to_sheet()
```

#### Step 5: Run the Script

```bash
export AGENTHR_API_KEY="your_api_key"
python sheets_sync.py
```

---

## Advanced Features

### Two-Way Sync

Enable updates from sheet back to AgentHR:

```javascript
// Add this to AgentHR.gs

/**
 * Check for changes in sheet and update AgentHR
 */
function syncSheetToAgentHR() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Candidates');

  // Get all data
  const data = sheet.getDataRange().getValues();
  const headers = data[0];

  // Find "Update" column
  const updateColIndex = headers.indexOf('Update');
  if (updateColIndex === -1) return;

  // Process rows marked for update
  for (let i = 1; i < data.length; i++) {
    const row = data[i];

    if (row[updateColIndex] === 'YES') {
      const candidateId = row[headers.indexOf('ID')];
      const newStage = row[headers.indexOf('Current Stage')];
      const vacancyId = row[headers.indexOf('Vacancy ID')];

      try {
        updateCandidateStage(candidateId, newStage, vacancyId);

        // Clear the update flag
        sheet.getRange(i + 1, updateColIndex + 1).setValue('UPDATED ✓');

        Logger.log(`Updated candidate ${candidateId}`);
      } catch (e) {
        Logger.log(`Failed to update candidate: ${e.message}`);
        sheet.getRange(i + 1, updateColIndex + 1).setValue('ERROR: ' + e.message);
      }
    }
  }
}
```

### Custom Reports

Create specialized reports:

```javascript
/**
 * Generate weekly hiring report
 */
function generateWeeklyReport() {
  const endDate = new Date();
  const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000);

  const analytics = fetchAnalytics(
    startDate.toISOString().split('T')[0],
    endDate.toISOString().split('T')[0]
  );

  const candidates = fetchCandidates(500);
  const newCandidates = candidates.filter(c => {
    const createdAt = new Date(c.created_at);
    return createdAt >= startDate && createdAt <= endDate;
  });

  const hiredCount = candidates.filter(c => {
    return c.current_stage === 'Hired' &&
           new Date(c.updated_at) >= startDate;
  }).length;

  // Create report sheet
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.insertSheet(`Week ${startDate.toLocaleDateString()}`);

  sheet.getRange('A1').setValue('Weekly Hiring Report');
  sheet.getRange('A1').setFontWeight('bold').setFontSize(16);

  sheet.getRange('A3').setValue('Period:');
  sheet.getRange('B3').setValue(`${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`);

  sheet.getRange('A5').setValue('New Candidates:');
  sheet.getRange('B5').setValue(newCandidates.length);

  sheet.getRange('A6').setValue('Hired:');
  sheet.getRange('B6').setValue(hiredCount);

  sheet.getRange('A7').setValue('Time to Hire:');
  sheet.getRange('B7').setValue(analytics.time_to_hire?.avg_days || 'N/A');

  sheet.autoResizeColumns(1, 2);
}
```

### Conditional Formatting

Add visual indicators to your sheet:

```javascript
/**
 * Apply conditional formatting to Candidates sheet
 */
function formatCandidateSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('Candidates');

  // Highlight hired candidates in green
  const rule = SpreadsheetApp.newConditionalFormatRule()
    .setRanges([sheet.getRange('E2:E1000')])
    .whenTextEqualTo('Hired')
    .setBackground('#d4edda')
    .build();

  sheet.setConditionalFormatRules([rule]);
}
```

## Troubleshooting

**"Script function not found" error:**
- Make sure the function name in the trigger matches exactly
- Check for typos in the function name

**Rate limiting errors:**
- Increase cache duration in `fetchCandidates()`
- Reduce sync frequency in triggers

**Authentication errors:**
- Verify your API key is valid
- For service accounts, ensure the sheet is shared with the service account email

**Data not updating:**
- Check the Execution log (View > Logs)
- Manually run the function to see error messages
- Clear cache and try again

## Resources

- [Google Apps Script Documentation](https://developers.google.com/apps-script)
- [Sheets API Reference](https://developers.google.com/sheets/api)
- [AgentHR API Reference](/api/endpoints.md)
