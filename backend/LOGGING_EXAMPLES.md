# Logging Examples - Real-world Scenarios

This document shows examples of log output for common scenarios in the Admin Timetable OCR AI feature.

## Scenario 1: Successful Timetable Upload Flow

### Step 1: File Upload Received
```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Timetable image upload received",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "content_type": "image/jpeg",
  "filename": "fall_2024_timetable.jpg"
}
```

### Step 2: File Content Read
```json
{
  "timestamp": "2024-01-15T10:30:45.234567Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "File content read",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_size_bytes": 2048576,
  "file_size_mb": 1.95
}
```

### Step 3: OCR Parsing Started
```json
{
  "timestamp": "2024-01-15T10:30:45.345678Z",
  "level": "INFO",
  "logger": "app.services.ocr",
  "message": "OCR parsing started",
  "file_size_bytes": 2048576,
  "api_provider": "Groq",
  "model": "llama-3.2-90b-vision-preview"
}
```

### Step 4: API Request Sent
```json
{
  "timestamp": "2024-01-15T10:30:45.456789Z",
  "level": "INFO",
  "logger": "app.services.ocr",
  "message": "Sending request to Groq API",
  "api_endpoint": "https://api.groq.com/openai/v1/chat/completions",
  "model": "llama-3.2-90b-vision-preview"
}
```

### Step 5: API Response Received
```json
{
  "timestamp": "2024-01-15T10:30:47.801234Z",
  "level": "INFO",
  "logger": "app.services.ocr",
  "message": "Groq API response received",
  "api_response_time_seconds": 2.345,
  "status_code": 200
}
```

### Step 6: OCR Completed Successfully
```json
{
  "timestamp": "2024-01-15T10:30:47.912345Z",
  "level": "INFO",
  "logger": "app.services.ocr",
  "message": "OCR parsing completed successfully",
  "total_duration_seconds": 2.567,
  "entries_extracted": 15,
  "extracted_text_length": 842
}
```

### Step 7: Upload Parsing Completed
```json
{
  "timestamp": "2024-01-15T10:30:48.023456Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Timetable upload parsing completed",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "entries_parsed": 15,
  "entries_skipped": 0,
  "extracted_text_length": 842
}
```

---

## Scenario 2: Successful Database Transaction

### Step 1: Confirmation Started
```json
{
  "timestamp": "2024-01-15T10:35:12.123456Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Timetable confirmation started",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "entries_to_save": 15
}
```

### Step 2: Transaction Started
```json
{
  "timestamp": "2024-01-15T10:35:12.234567Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Database transaction started",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "transaction_type": "atomic_timetable_replacement"
}
```

### Step 3: Deleting Existing Entries
```json
{
  "timestamp": "2024-01-15T10:35:12.345678Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Deleting existing timetable entries",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

### Step 4: Existing Entries Deleted
```json
{
  "timestamp": "2024-01-15T10:35:12.456789Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Existing timetable entries deleted",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "deleted_count": 18
}
```

### Step 5: Inserting New Entries
```json
{
  "timestamp": "2024-01-15T10:35:12.567890Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Inserting new timetable entries",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "entries_to_insert": 15,
  "entries_skipped": 0
}
```

### Step 6: Committing Transaction
```json
{
  "timestamp": "2024-01-15T10:35:12.678901Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Committing database transaction",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "transaction_type": "atomic_timetable_replacement"
}
```

### Step 7: Transaction Committed Successfully
```json
{
  "timestamp": "2024-01-15T10:35:12.789012Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Database transaction committed successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "entries_created": 15,
  "entries_skipped": 0,
  "deleted_count": 18
}
```

---

## Scenario 3: File Upload Rejected - Size Limit Exceeded

```json
{
  "timestamp": "2024-01-15T10:40:30.123456Z",
  "level": "WARNING",
  "logger": "app.routers.academic",
  "message": "File upload rejected - exceeds size limit",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_size_bytes": 11534336,
  "file_size_mb": 11.0,
  "max_size_mb": 10
}
```

---

## Scenario 4: OCR Parsing Error

### JSON Parsing Failed
```json
{
  "timestamp": "2024-01-15T10:45:15.123456Z",
  "level": "ERROR",
  "logger": "app.services.ocr",
  "message": "JSON parsing failed - unable to extract structured data",
  "exception_type": "JSONDecodeError",
  "exception_message": "Expecting value: line 1 column 1 (char 0)",
  "raw_response_text": "I see a timetable in the image, but I cannot extract structured data from it...",
  "stack_trace": "Traceback (most recent call last):\n  File \"app/services/ocr.py\", line 120..."
}
```

### OCR Completed But No Entries
```json
{
  "timestamp": "2024-01-15T10:45:17.234567Z",
  "level": "WARNING",
  "logger": "app.services.ocr",
  "message": "OCR completed but could not parse structured data",
  "total_duration_seconds": 3.456,
  "extracted_text_length": 245
}
```

### Upload Failed - No Entries Extracted
```json
{
  "timestamp": "2024-01-15T10:45:17.345678Z",
  "level": "WARNING",
  "logger": "app.routers.academic",
  "message": "OCR completed but no entries extracted",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "extracted_text_length": 245
}
```

---

## Scenario 5: Database Transaction Failure

### Transaction Failed
```json
{
  "timestamp": "2024-01-15T10:50:22.123456Z",
  "level": "ERROR",
  "logger": "app.routers.academic",
  "message": "Database transaction failed - rolling back",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "exception_type": "OperationalError",
  "exception_message": "database connection timeout",
  "transaction_type": "atomic_timetable_replacement"
}
```

### Transaction Rolled Back
```json
{
  "timestamp": "2024-01-15T10:50:22.234567Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Database transaction rolled back",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

---

## Scenario 6: Entry Validation Warnings

### During Upload
```json
{
  "timestamp": "2024-01-15T10:55:10.123456Z",
  "level": "WARNING",
  "logger": "app.routers.academic",
  "message": "Entry parsing failed - skipping entry",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "exception_type": "ValueError",
  "exception_message": "time data 'invalid' does not match format '%H:%M'",
  "entry_data": {
    "day_of_week": "Monday",
    "start_time": "invalid",
    "end_time": "10:30",
    "subject": "Math"
  }
}
```

### During Confirmation
```json
{
  "timestamp": "2024-01-15T11:00:15.123456Z",
  "level": "WARNING",
  "logger": "app.routers.academic",
  "message": "Entry validation failed - skipping entry",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "department_id": "660e8400-e29b-41d4-a716-446655440001",
  "exception_type": "ValueError",
  "exception_message": "start_time must be before end_time"
}
```

---

## Scenario 7: API Timeout

```json
{
  "timestamp": "2024-01-15T11:05:45.123456Z",
  "level": "ERROR",
  "logger": "app.services.ocr",
  "message": "OCR extraction timeout",
  "exception_type": "TimeoutError",
  "exception_message": "Request timed out after 30 seconds",
  "total_duration_seconds": 30.123,
  "timeout_limit_seconds": 30,
  "stack_trace": "Traceback (most recent call last):\n  File \"app/services/ocr.py\", line 85..."
}
```

---

## Using These Logs for Analysis

### Query: Find all uploads by a specific user
```
user_id:"550e8400-e29b-41d4-a716-446655440000" AND message:"upload"
```

### Query: Find slow OCR operations (>5 seconds)
```
message:"OCR parsing completed" AND total_duration_seconds:>5
```

### Query: Find all errors in the last hour
```
level:ERROR AND timestamp:>[now-1h]
```

### Query: Track a specific department's activity
```
department_id:"660e8400-e29b-41d4-a716-446655440001"
```

### Query: Find all transaction failures
```
level:ERROR AND transaction_type:"atomic_timetable_replacement"
```

### Query: Monitor validation errors
```
message:"validation failed" OR message:"parsing failed"
```

---

## Performance Metrics Tracking

From the logs above, you can track:

- **Average OCR Response Time**: Extract from `api_response_time_seconds`
- **Total Processing Time**: Extract from `total_duration_seconds`
- **Success Rate**: Count successes vs. errors
- **File Sizes**: Track `file_size_mb` distribution
- **Entries Per Upload**: Track `entries_extracted` and `entries_created`
- **Validation Failure Rate**: Count validation warnings vs. total entries

Example aggregation query (in Elasticsearch):
```json
{
  "aggs": {
    "avg_ocr_time": {
      "avg": {
        "field": "api_response_time_seconds"
      }
    },
    "success_count": {
      "filter": {
        "term": {
          "message": "Database transaction committed successfully"
        }
      }
    }
  }
}
```
