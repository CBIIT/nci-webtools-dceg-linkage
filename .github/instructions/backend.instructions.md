---
applyTo: "server"
---

# LDlink Backend Project Overview

This is a Flask-based Python backend for LDlink, a bioinformatics web application that provides various linkage disequilibrium (LD) analysis tools for population genetics research. The backend serves both REST API endpoints and web application endpoints.

## Folder Structure

- `/server`: Contains the Python Flask backend with bioinformatics analysis modules
  - Main Flask application: `LDlink.py` (primary app with all route definitions)
  - Analysis modules: `LDpair.py`, `LDproxy.py`, `LDmatrix.py`, `LDhap.py`, `LDassoc.py`, `LDexpress.py`, `LDtrait.py`, `LDpop.py`
  - Utility modules: `LDcommon.py`, `LDutilites.py`, `ApiAccess.py`
  - SNP analysis: `SNPchip.py`, `SNPclip.py`
  - Visualization: Bokeh-based plotting in `*_plot_sub.py` files
  - WSGI deployment: `LDlink.wsgi`

## Libraries and Frameworks

- **Flask**: Primary web framework for REST API and web endpoints
- **mod_wsgi**: WSGI server deployment
- **MongoDB (pymongo)**: Primary database for genomic data storage
- **Bokeh**: Interactive visualization library for genetic plots
- **NumPy**: Numerical computations for statistical analysis
- **Selenium**: Web scraping and automated browser interactions
- **Boto3**: AWS SDK for cloud storage integration
- **pybedtools**: Genomic interval manipulation
- **httpx/requests**: HTTP client libraries
- **cairosvg/svgutils**: SVG image processing
- **ldsc**: Linkage disequilibrium score regression (external git dependency)

## Architecture Patterns

- **Modular Analysis Functions**: Each LD analysis tool is implemented as a separate module with a `calculate_*` function
- **Token-based API Authentication**: User registration and API access token management
- **MongoDB Read-only Connections**: Database queries through connection pooling
- **Background Job Processing**: Long-running analysis tasks with status tracking
- **File Upload/Download**: Temporary file handling for large datasets
- **Configuration Management**: Environment-based configuration through `get_config()`

## Key API Endpoints

- `/LDlinkRest/*` and `/LDlinkRestWeb/*`: Dual REST/Web endpoints for each tool
- Analysis tools: `ldpair`, `ldproxy`, `ldmatrix`, `ldhap`, `ldassoc`, `ldexpress`, `ldtrait`, `ldpop`
- SNP tools: `snpchip`, `snpclip`
- Statistical tools: `ldscore`, `ldherit`, `ldcorrelation`
- Utility endpoints: `ping`, `upload`, `status`, file downloads

## Data Processing Patterns

- **Population Genetics**: Handle 1000 Genomes Project data, population stratification
- **Genomic Coordinates**: Work with chromosome positions, genomic builds (hg19/hg38)
- **SNP/Variant Processing**: RS numbers, chromosome:position format, allele frequencies
- **Statistical Analysis**: R² and D' calculations, p-values, confidence intervals
- **Large Dataset Handling**: Chunked processing, temporary file management

## Coding Standards

- Use descriptive function names reflecting genetic analysis (e.g., `calculate_pair`, `get_population_data`)
- Follow Python PEP 8 style guidelines
- Include comprehensive error handling for genetic data validation
- Use type hints for function parameters and return values
- Implement proper MongoDB connection management and cleanup
- Include logging for analysis progress and debugging
- Validate genomic inputs (RS numbers, coordinates, population codes)

## Security Considerations

- Implement rate limiting for API endpoints
- Validate and sanitize all user inputs, especially file uploads
- Use secure file handling with `werkzeug.utils.secure_filename`
- Implement token-based authentication with expiration
- Block malicious users through IP and token tracking
- Sanitize database queries to prevent injection attacks

## Performance Guidelines

- Use MongoDB indexes for fast genomic coordinate lookups
- Implement connection pooling for database access
- Cache frequently accessed population and genomic reference data
- Use background processing for computationally intensive analyses
- Implement proper cleanup of temporary files
- Monitor memory usage for large genomic datasets

## Testing Considerations

- Test with various genomic input formats (RS numbers, coordinates)
- Validate calculations against known genetic datasets
- Test API rate limiting and authentication flows
- Verify file upload/download functionality
- Test edge cases with invalid genomic coordinates
- Ensure proper cleanup of temporary analysis files