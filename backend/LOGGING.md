# Comprehensive Logging Documentation

## Overview

The Admin Timetable OCR AI feature implements comprehensive structured logging in JSON format for debugging and monitoring. All logs are outputted to stdout in JSON format, making them easily parseable by log aggregation systems (e.g., ELK Stack, CloudWatch, Datadog).

## Logging Architecture

### Structured JSON Format

All logs follow a consistent JSON structure:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "app.routers.academic",
  "message": "Human-readable log message",
  "user_id": "uuid-123",
  "department_id": "uuid-456",
  "custom_field_1": "value1",
  "custom_field_2": 123
}
```

### Key Components

1. **StructuredLogger** (`app/core/logging_config.py`)
   - Wrapper class for Python's logging module
   - Automatically formats logs as JSON
   - Supports arbitrary key-value pairs for context

2. **JSONFormatter** (`app/core/logging_config.py`)
   - Custom logging formatter
   - Converts log records to JSON format
   - Includes timestamp, level, logger name, message, and extra fields

## Logged Events

### 1. File Upload Metadata

**Location**: `app/routers/academic.py` - `upload_timetable_image()`

**Events Logged**:

#### Upload Received
```json
{
  "message": "Timetable image upload received",
  "user_id": "user-uuid",
  "department_id": "dept-uuid",
  "content_type": "image/jpeg",
  "filename": "timetable.jpg"
}
```

#### File Content Read
```json
{
  "message": "File content read",
  "user_id": "user-uuid",
  "file_size_bytes": 1048576,
  "file_size_mb": 1.0
}
```

#### Upload Rejected (Various Reasons)
```json
{
  "level": "WARNING",
  "message": "File upload rejected - unsupported format",
  "user_id": "user-uuid",
  "content_type": "image/gif",
  "filename": "timetable.gif"
}
```

```json
{
  "level": "WARNING",
  "message": "File upload rejected - exceeds size limit",
  "user_id": "user-uuid",
  "file_size_bytes": 11534336,
  "file_size_mb": 11.0,
  "max_size_mb": 10
}
```

### 2. OCR API Request/Response Timings

**Location**: `app/services/ocr.py` - `parse_timetable_image()`

**Events Logged**:

#### OCR Parsing Started
```json
{
  "message": "OCR parsing started",
  "file_size_bytes": 1048576,
  "api_provider": "Groq",
  "model": "llama-3.2-90b-vision-preview"
}
```

#### API Request Sent
```json
{
  "message": "Sending request to Groq API",
  "api_endpoint": "https://api.groq.com/openai/v1/chat/completions",
  "model": "llama-3.2-90b-vision-preview"
}
```

#### API Response Received
```json
{
  "message": "Groq API response received",
  "api_response_time_seconds": 2.345,
  "status_code": 200
}
```

#### OCR Completed Successfully
```json
{
  "message": "OCR parsing completed successfully",
  "total_duration_seconds": 2.567,
  "entries_extracted": 15,
  "extracted_text_length": 450
}
```

### 3. Parsing Errors with Extracted Text

**Location**: `app/services/ocr.py` - `parse_timetable_image()`

**Events Logged**:

#### JSON Parsing Failed
```json
{
  "level": "ERROR",
  "message": "JSON parsing failed - unable to extract structured data",
  "exception_type": "JSONDecodeError",
  "exception_message": "Expecting value: line 1 column 1 (char 0)",
  "raw_response_text": "First 500 chars of raw response...",
  "stack_trace": "Full stack trace here..."
}
```

#### OCR Timeout
```json
{
  "level": "ERROR",
  "message": "OCR extraction timeout",
  "exception_type": "TimeoutError",
  "exception_message": "Request timed out",
  "total_duration_seconds": 30.123,
  "timeout_limit_seconds": 30,
  "stack_trace": "Full stack trace here..."
}
```

#### General OCR Failure
```json
{
  "level": "ERROR",
  "message": "OCR parsing failed",
  "exception_type": "HTTPError",
  "exception_message": "401 Unauthorized",
  "total_duration_seconds": 1.234,
  "stack_trace": "Full stack trace here..."
}
```

#### No Entries Extracted Warning
```json
{
  "level": "WARNING",
  "message": "OCR completed but could not parse structured data",
  "total_duration_seconds": 2.456,
  "extracted_text_length": 120
}
```

### 4. Database Transaction Events

**Location**: `app/routers/academic.py` - `confirm_timetable()`

**Events Logged**:

#### Transaction Started
```json
{
  "message": "Database transaction started",
  "user_id": "user-uuid",
  "department_id": "dept-uuid",
  "transaction_type": "atomic_timetable_replacement"
}
```

#### Deleting Existing Entries
```json
{
  "message": "Deleting existing timetable entries",
  "user_id": "user-uuid",
  "department_id": "dept-uuid"
}
```

#### Existing Entries Deleted
```json
{
  "message": "Existing timetable entries deleted",
  "user_id": "user-uuid",
  "department_id": "dept-uuid",
  "deleted_count": 20
}
```

#### Inserting New Entries
```json
{
  "message": "Inserting new timetable entries",
  "user_id": "user-uuid",
  "department_id": "dept-uuid",
  "entries_to_insert": 15,
  "entries_skipped": 2
}
```

#### Committing Transaction
```json
{
  "message": "Committing database transaction",
  "user_id": "user-uuid",
  "department_id": "dept-uuid",
  "transaction_type": "atomic_timetable_replacement"
}
```

#### Transaction Committed Successfully
```json
{
  "message": "Database transaction committed successfully",
  "user_id": "user-uuid",
  "department_id": "dept-uuid",
  "entries_created": 15,
  "entries_skipped": 2,
  "deleted_count": 20
}
```

#### Transaction Failed (Rollback)
```json
{
  "level": "ERROR",
  "message": "Database transaction failed - rolling back",
  "user_id": "user-uuid",
  "department_id": "dept-uuid",
  "exception_type": "IntegrityError",
  "exception_message": "Duplicate key violation",
  "transaction_type": "atomic_timetable_replacement"
}
```

#### Transaction Rolled Back
```json
{
  "message": "Database transaction rolled back",
  "user_id": "user-uuid",
  "department_id": "dept-uuid"
}
```

### 5. Entry Validation Warnings

**Location**: `app/routers/academic.py`

**Events Logged**:

#### Entry Parsing Failed (Upload)
```json
{
  "level": "WARNING",
  "message": "Entry parsing failed - skipping entry",
  "user_id": "user-uuid",
  "exception_type": "ValueError",
  "exception_message": "Invalid time format",
  "entry_data": {"day_of_week": "Monday", "start_time": "invalid"}
}
```

#### Entry Validation Failed (Confirm)
```json
{
  "level": "WARNING",
  "message": "Entry validation failed - skipping entry",
  "user_id": "user-uuid",
  "department_id": "dept-uuid",
  "exception_type": "ValueError",
  "exception_message": "start_time must be before end_time"
}
```

## Usage Examples

### Using the StructuredLogger

```python
from app.core.logging_config import StructuredLogger

# Create logger instance
logger = StructuredLogger(__name__)

# Log with metadata
logger.info(
    "User action performed",
    user_id="123",
    action="upload",
    resource_type="timetable",
    duration_ms=450
)

# Log error with context
logger.error(
    "Database query failed",
    query_type="SELECT",
    table="timetables",
    exception_type="OperationalError",
    exception_message="connection timeout"
)

# Log warning
logger.warning(
    "Rate limit approaching",
    user_id="123",
    requests_count=95,
    limit=100
)
```

### Querying Logs

If using a log aggregation system, you can query logs like:

**Find all failed uploads for a user:**
```
level:ERROR AND message:"upload" AND user_id:"user-uuid-123"
```

**Find slow OCR requests (>5 seconds):**
```
message:"OCR parsing completed" AND total_duration_seconds:>5
```

**Find database transaction failures:**
```
level:ERROR AND transaction_type:"atomic_timetable_replacement"
```

**Track a specific user's activity:**
```
user_id:"user-uuid-123"
```

## Benefits of Structured Logging

1. **Easy Parsing**: JSON format is machine-readable
2. **Rich Context**: Each log includes relevant metadata
3. **Searchable**: Log aggregation systems can index and search all fields
4. **Monitoring**: Can create alerts based on specific log patterns
5. **Debugging**: Full context available for troubleshooting
6. **Audit Trail**: Track user actions and system state changes
7. **Performance Analysis**: Measure API response times and database operations

## Best Practices

1. **Always include user_id** when available for audit trails
2. **Always include department_id** for timetable operations
3. **Log timing information** for performance monitoring
4. **Include exception details** for errors (type, message, stack trace)
5. **Log transaction boundaries** (start, commit, rollback)
6. **Use appropriate log levels**:
   - INFO: Normal operations
   - WARNING: Recoverable issues (validation failures, retries)
   - ERROR: Failures that prevent operation completion
7. **Limit sensitive data**: Don't log passwords, tokens, or full file contents

## Integration with Log Aggregation

The JSON format makes it easy to integrate with popular log aggregation systems:

- **ELK Stack**: Parse JSON logs with Logstash
- **AWS CloudWatch**: Use CloudWatch Insights to query JSON logs
- **Datadog**: Automatic JSON parsing and field indexing
- **Splunk**: JSON auto-extraction
- **Google Cloud Logging**: Structured logging support

Example Logstash configuration:
```
input {
  stdin {
    codec => json
  }
}

filter {
  date {
    match => [ "timestamp", "ISO8601" ]
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "timetable-logs-%{+YYYY.MM.dd}"
  }
}
```

## Testing

Run the logging test to verify structured logging works:

```bash
cd backend
python test_logging.py
```

Expected output: JSON-formatted logs with proper structure.
