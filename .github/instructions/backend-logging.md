---
applyTo: "server/*,docker/backend.dockerfile,docker/wsgi.conf"
---

# LDlink Backend Logging Guidelines

## Logging Philosophy

Log flask/mod-wsgi API and Python modules to support:

- **Fast root cause analysis** - Enable quick identification of issues
- **Traceability** - Track request flow and data transformations
- **Performance monitoring** - Measure execution times and resource usage
- **Improve consistency and developer productivity** - Standardized patterns across modules

## Log Level Usage

### DEBUG
- **Purpose**: Internal details for development/testing environments
- **When to use**: 
  - Function entry/exit points
  - Variable state during processing
  - Database query parameters (sanitized)
  - Subprocess execution details
- **Production**: Avoid in production environments
- **AI Note**: Avoid generating DEBUG logs using AI - these should be manually added for specific debugging needs

### INFO
- **Purpose**: Key checkpoints and business logic events
- **When to use**:
  - API request start/completion with timing
  - User actions (login, logout, token usage)
  - Service start/stop events
  - Database operation results (counts, success/failure)
  - File operations (uploads, downloads, cleanup)
  - External API calls and responses
- **Examples**:
  - `"Executed LDmatrix (1.53s)"`
  - `"User token validated for LDproxy request"`
  - `"Retrieved 150 SNPs from database"`

### WARNING
- **Purpose**: Unexpected but recoverable situations
- **When to use**:
  - Invalid input parameters that can be corrected
  - Deprecated feature usage
  - Performance degradation indicators
  - Resource usage approaching limits
- **Examples**:
  - `"Invalid SNP format provided, attempting correction"`
  - `"Database connection pool at 80% capacity"`

### ERROR
- **Purpose**: Operation failures that prevent normal execution
- **When to use**:
  - API failures
  - Database connection errors
  - File system errors
  - External service failures
  - Authentication/authorization failures
- **Examples**:
  - `"Database connection failed: connection timeout"`
  - `"Failed to process SNP list: invalid format"`

## Log Format

### Standard Format
```
"[{module_name}] [{timestamp}] [{log_level}] - {message}"
```

### Examples
```
[ldmatrix] [2025-01-15 14:30:22] [INFO] - Executed LDmatrix (1.53s)
[ldproxy] [2025-01-15 14:30:25] [ERROR] - Failed to retrieve SNP data: connection timeout
[cleanup] [2025-01-15 14:30:30] [INFO] - Deleted 5 temporary files for request abc123
```

## Module-Specific Logging Patterns

### API Endpoints
```python
# At function start
app.logger.info(f"Starting {function_name} request")

# For timing
start_time = time.time()
# ... processing ...
execution_time = round(time.time() - start_time, 2)
app.logger.info(f"Executed {function_name} ({execution_time}s)")

# For errors
app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
```

### Database Operations
```python
# Before query
app.logger.debug(f"Executing query: {sanitized_query}")

# After query
app.logger.info(f"Retrieved {len(results)} records from {collection_name}")

# On error
app.logger.error(f"Database operation failed: {error_message}")
```

### File Operations
```python
# File creation
app.logger.info(f"Created output file: {file_path}")

# File cleanup
app.logger.info(f"Cleaned up {file_count} temporary files")

# File errors
app.logger.error(f"Failed to write file {file_path}: {error}")
```

## Security Guidelines

### What NOT to Log
- **PII (Personally Identifiable Information)**: Names, emails, addresses
- **Access keys**: API tokens, passwords, private keys
- **Sensitive data**: Personal genetic information, health data
- **Full request bodies**: Log only essential parameters
- **Stack traces in production**: Use ERROR level with sanitized messages

### What to Log (Safely)
- **Request metadata**: Method, endpoint, user agent (sanitized)
- **Performance metrics**: Timing, resource usage
- **Error types**: Exception class names, error codes
- **Business events**: User actions, system state changes

### Sanitization Examples
```python
# Good - log essential info only
app.logger.info(f"User {user_id} accessed LDproxy endpoint")

# Bad - log sensitive data
app.logger.info(f"User {email} with token {api_token} accessed endpoint")

# Good - log request parameters safely
app.logger.debug(f"LDmatrix request: {len(snp_list)} SNPs, population: {population}")

# Bad - log full request body
app.logger.debug(f"Request body: {request.get_json()}")
```

## Performance Considerations

### Log Volume Management
- **Avoid excessive logging**: Don't log every loop iteration
- **Use appropriate levels**: DEBUG for development, INFO for production
- **Batch operations**: Log summary rather than individual items
- **Conditional logging**: Use log level checks for expensive operations

### Examples
```python
# Good - log summary
app.logger.info(f"Processed {total_count} SNPs in {execution_time}s")

# Bad - log every item
for snp in snp_list:
    app.logger.debug(f"Processing SNP: {snp}")  # Too verbose

# Good - conditional debug logging
if app.logger.isEnabledFor(logging.DEBUG):
    app.logger.debug(f"Detailed processing info: {expensive_operation()}")
```

## Error Handling Patterns

### Structured Error Logging
```python
try:
    result = process_data(input_data)
    app.logger.info(f"Successfully processed {len(result)} items")
except ValueError as e:
    app.logger.warning(f"Invalid input format: {str(e)}")
    return error_response("Invalid input format")
except DatabaseError as e:
    app.logger.error(f"Database operation failed: {str(e)}")
    return error_response("Database error")
except Exception as e:
    app.logger.error(f"Unexpected error in {function_name}: {str(e)}")
    app.logger.error("".join(traceback.format_exception(None, e, e.__traceback__)))
    return error_response("Internal server error")
```

## Context and Correlation

### Request Tracking
```python
# Add request ID to all logs
request_id = generate_request_id()
app.logger.info(f"[{request_id}] Starting LDmatrix request")

# Pass request context to helper functions
def process_snps(snp_list, request_id):
    app.logger.debug(f"[{request_id}] Processing {len(snp_list)} SNPs")
```

### Module Identification
```python
# Use consistent module names
logger = logging.getLogger("ldmatrix")  # Instead of "root"
logger.info("Starting matrix calculation")
```

## Best Practices Summary

1. **Consistency**: Use the same patterns across all modules
2. **Timing**: Always log execution time for API endpoints
3. **Context**: Include relevant identifiers (request ID, user ID, etc.)
4. **Sanitization**: Never log sensitive data
5. **Levels**: Use appropriate log levels for different environments
6. **Performance**: Avoid excessive logging in production
7. **Errors**: Always log full error details in development, sanitized in production
8. **Traceability**: Enable request flow tracking through correlation IDs

## Implementation Checklist

When adding logging to new code:

- [ ] Use consistent module names in logger initialization
- [ ] Include timing for API endpoints
- [ ] Sanitize all logged data
- [ ] Use appropriate log levels
- [ ] Add error handling with proper logging
- [ ] Include relevant context (request ID, user info)
- [ ] Test logging in both development and production environments
