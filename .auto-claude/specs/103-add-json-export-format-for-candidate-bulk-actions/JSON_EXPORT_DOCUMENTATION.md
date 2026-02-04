# JSON Export Format for Candidate Bulk Actions - User Guide

## Overview

The AgentHR platform supports exporting candidate data in both JSON and CSV formats through bulk actions. JSON export provides machine-readable data ideal for integrations and automated processing.

## Frontend Usage (Web Interface)

### Step-by-Step Guide

1. **Navigate to Candidate Search**
   - Go to the Candidates page
   - Use search filters to find the candidates you want to export

2. **Select Candidates**
   - Click the checkboxes next to candidate names
   - Use "Select All" to export all candidates in current results

3. **Initiate Export**
   - Click the "Export" button in the bulk actions toolbar
   - A dialog will appear with format options

4. **Choose Export Format**
   - **JSON**: Machine-readable format, preserves data types, ideal for API integrations
   - **CSV**: Spreadsheet-friendly format, suitable for Excel/Google Sheets

5. **Download**
   - Click "Export" button
   - File will download as `candidates_export.json` or `candidates_export.csv`

### Exported Data Structure

**JSON Format:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "john_doe_resume.pdf",
    "current_stage": "screening",
    "stage_name": "Screening",
    "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T14:20:00Z",
    "tags": ["Senior Level", "Python Expert"]
  }
]
```

**CSV Format:**
```csv
id,filename,current_stage,stage_name,vacancy_id,created_at,updated_at,tags
550e8400-e29b-41d4-a716-446655440000,john_doe_resume.pdf,screening,Screening,650e8400-e29b-41d4-a716-446655440000,2026-01-15T10:30:00Z,2026-01-15T14:20:00Z,"Senior Level,Python Expert"
```

## Backend Usage (API)

### Endpoint

```
POST /api/candidates/bulk-action
```

### Request Format

```json
{
  "resume_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ],
  "action": "export",
  "export_format": "json"
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `resume_ids` | array | Yes | Array of candidate resume UUIDs |
| `action` | string | Yes | Must be `"export"` |
| `export_format` | string | No | `"json"` (default) or `"csv"` |

### Response Format

**Success Response (200 OK):**
```json
{
  "action": "export",
  "total_requested": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "resume_id": "550e8400-e29b-41d4-a716-446655440000",
      "success": true,
      "message": "Candidate data exported",
      "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "filename": "resume.pdf",
        "current_stage": "screening",
        "stage_name": "Screening",
        "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
        "created_at": "2026-01-15T10:30:00Z",
        "updated_at": "2026-01-15T14:20:00Z",
        "tags": ["Senior Level"]
      }
    }
  ],
  "export_data": {
    "format": "json",
    "data": [...],
    "count": 2
  }
}
```

### cURL Examples

**Export to JSON:**
```bash
curl -X POST http://localhost:8000/api/candidates/bulk-action \
  -H "Content-Type: application/json" \
  -d '{
    "resume_ids": ["uuid1", "uuid2", "uuid3"],
    "action": "export",
    "export_format": "json"
  }'
```

**Export to CSV:**
```bash
curl -X POST http://localhost:8000/api/candidates/bulk-action \
  -H "Content-Type: application/json" \
  -d '{
    "resume_ids": ["uuid1", "uuid2", "uuid3"],
    "action": "export",
    "export_format": "csv"
  }'
```

### Python Example

```python
import requests
import json

def export_candidates(resume_ids, format='json'):
    """Export candidates in specified format"""
    response = requests.post(
        'http://localhost:8000/api/candidates/bulk-action',
        json={
            'resume_ids': resume_ids,
            'action': 'export',
            'export_format': format
        }
    )
    response.raise_for_status()
    return response.json()

# Usage
result = export_candidates(['uuid1', 'uuid2', 'uuid3'], format='json')

# Access exported data
if result['export_data']['format'] == 'json':
    candidates = result['export_data']['data']
    print(f"Exported {len(candidates)} candidates")

    # Save to file
    with open('candidates_export.json', 'w') as f:
        json.dump(candidates, f, indent=2)
```

### JavaScript Example

```javascript
async function exportCandidates(resumeIds, format = 'json') {
  const response = await fetch('http://localhost:8000/api/candidates/bulk-action', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      resume_ids: resumeIds,
      action: 'export',
      export_format: format
    })
  });

  if (!response.ok) {
    throw new Error(`Export failed: ${response.statusText}`);
  }

  return await response.json();
}

// Usage
const result = await exportCandidates(['uuid1', 'uuid2'], 'json');

// Download as file
if (result.export_data.format === 'json') {
  const blob = new Blob([JSON.stringify(result.export_data.data, null, 2)], {
    type: 'application/json'
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'candidates_export.json';
  a.click();
}
```

## Use Cases

### When to Use JSON Format

1. **API Integrations**: Feed candidate data into other systems
2. **Automated Processing**: Parse and process candidate data programmatically
3. **Data Migration**: Transfer data between systems
4. **Machine Learning**: Use as training data for ML models
5. **Type Preservation**: Maintain data types (dates, arrays, etc.)

### When to Use CSV Format

1. **Spreadsheet Analysis**: Open in Excel, Google Sheets, etc.
2. **Business Reporting**: Share with non-technical stakeholders
3. **Data Visualization**: Import into BI tools (Tableau, Power BI)
4. **Simple Filtering**: Basic row/column filtering needs

## Data Fields

The export includes the following fields for each candidate:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique candidate identifier (UUID) |
| `filename` | string | Original resume filename |
| `current_stage` | string | Current workflow stage ID |
| `stage_name` | string | Human-readable stage name |
| `vacancy_id` | string | Associated vacancy UUID (nullable) |
| `created_at` | string | ISO 8601 timestamp when candidate was added |
| `updated_at` | string | ISO 8601 timestamp of last stage change |
| `tags` | array | List of tag names assigned to candidate |

## Error Handling

### Common Errors

**Invalid Resume ID:**
```json
{
  "resume_id": "invalid-id",
  "success": false,
  "message": "Invalid candidate ID format: invalid-id",
  "data": null
}
```

**Candidate Not Found:**
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": false,
  "message": "Candidate not found: 550e8400-e29b-41d4-a716-446655440000",
  "data": null
}
```

**Mixed Success/Failure:**
```json
{
  "action": "export",
  "total_requested": 3,
  "successful": 2,
  "failed": 1,
  "results": [...]
}
```

## Best Practices

1. **Batch Size**: Limit exports to 100-200 candidates per request for optimal performance
2. **Error Handling**: Always check `successful` and `failed` counts in response
3. **Data Validation**: Verify `export_data.count` matches expected number of candidates
4. **File Naming**: Use descriptive filenames with timestamps: `candidates_export_2026-01-15.json`
5. **Format Selection**: Choose JSON for machine processing, CSV for human analysis

## Related Documentation

- [API Reference](../../backend/docs/API_REFERENCE.md#bulk-action-on-candidates)
- [API Usage Guide](../../docs/API_USAGE_GUIDE.md#bulk-export-candidates-json-or-csv)
- [Bulk Actions Component](../../frontend/src/components/BulkCandidateActions.tsx)

---

**Last Updated:** 2026-02-04
**Feature Version:** 1.0.0
