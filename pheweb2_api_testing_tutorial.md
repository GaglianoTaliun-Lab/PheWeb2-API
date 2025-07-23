# PheWeb 2.0 API Testing Tutorial with Example Data

## Overview
This tutorial will guide you through setting up and testing the PheWeb 2.0 API using the provided example REGENIE data file (`BLD_nonHDL_COM.regenie.gz`). (Location: `/lustre06/project/6060121/CLSA_PheWeb_shared/Cleaned/GWAS/EUR/Continuous/Combined/GWAS_results_bin_both_2/GWAS/results/BLD_nonHDL_COM.regenie.gz`)

## Prerequisites
- Python 3.12+ installed
- Linux-based OS (recommended)
- Git installed

## Step 1: Initial Setup

### 1.1 Clone and Setup Repository
```bash
# Clone the repository
git clone https://github.com/GaglianoTaliun-Lab/PheWeb2.0-API.git
cd PheWeb2.0-API

# Create and activate Python virtual environment
python -m venv .venv
source .venv/bin/activate

# Install PheWeb2 Python package and dependencies
pip install -e .
```

## Step 2: Prepare Example Data

### 2.1 Verify Example Data Structure
Your example data file `tests/example_data/BLD_nonHDL_COM.regenie.gz` contains the following columns:
- **CHROM**: Chromosome (Required)
- **GENPOS**: Genomic position (Required) 
- **ID**: Variant identifier
- **ALLELE0**: Reference allele (Required)
- **ALLELE1**: Effect allele (Required)
- **A1FREQ**: Allele frequency
- **INFO**: Imputation quality score
- **N**: Sample size
- **TEST**: Statistical test (Required)
- **BETA**: Effect size (Required)
- **SE**: Standard error (Required)
- **CHISQ**: Chi-square statistic
- **LOG10P**: -log10 p-value (Required)
- **EXTRA**: Additional information

All required fields are present! 

### 2.2 Create Directory Structure
```bash
# Create the main data directory
mkdir -p /var/local/CLSA_PheWeb_data/generated_by_pheweb

# Or use a local directory for testing
mkdir -p ./test_data/generated_by_pheweb
```

## Step 3: Configuration Setup

### 3.1 Create Environment File
Create a `.env` file in the project root:

```bash
# .env file content
BASE_DIR=/var/local/CLSA_PheWeb_data/generated_by_pheweb
# Or for local testing:
# BASE_DIR=./test_data/generated_by_pheweb

CORS_ORIGINS=http://localhost:3000,http://localhost:8080
R2_DIR=  # Leave empty if no R2 file available
```

### 3.2 Verify config.py
Ensure your `config.py` matches the field structure of your data:

```python
field_aliases = {
    "CHROM": "chrom",
    "GENPOS": "pos", 
    "ALLELE0": "ref",
    "ALLELE1": "alt",
    "A1FREQ": "af",
    "INFO": "imp_quality",  # Using INFO from REGENIE output
    "N": "n_samples",
    "BETA": "beta",
    "SE": "sebeta",
    "LOG10P": "pval",
    "TEST": "test",
}
```

## Step 4: Create Phenotype List

### 4.1 Create pheno-list.csv
Create a `pheno-list.csv` file in the project root:

```csv
phenocode,phenostring,assoc_files,num_samples,num_cases,num_controls,category
BLD_nonHDL_COM,Blood Non-HDL Cholesterol Combined,tests/example_data/BLD_nonHDL_COM.regenie.gz,12278,,,blood_lipids
```

### 4.2 Generate JSON Phenotype List
```bash
# Generate the JSON phenotype list from CSV
pheweb2 phenolist import-phenolist pheno-list.csv
```

This creates `pheno-list.json` in your project root.

## Step 5: Data Preprocessing

### 5.1 Run Preprocessing
```bash
# Process all files for the backend server
pheweb process
```

This command will:
- Parse the REGENIE file
- Apply quality filters (imputation quality ≥ 0.3 by default)
- Generate Manhattan plot data
- Create QQ plot data  
- Generate top hits and loci data
- Create phenotype summaries

### 5.2 Generate Autocomplete Database (Optional)
```bash
# Create autocomplete database for variant/rsID searching
pheweb generate-autocomplete-db
```

## Step 6: Verify Generated Data

### 6.1 Check Directory Structure
After preprocessing, verify these directories exist:

```bash
ls -la /var/local/CLSA_PheWeb_data/generated_by_pheweb/
# Or: ls -la ./test_data/generated_by_pheweb/

# Expected directories:
# ├── manhattan/
# ├── qq/  
# ├── pheno_gz/
# ├── best_of_pheno/
# ├── sites/
# ├── phenotypes.json
# ├── top_hits.json
# └── autocomplete.db (if generated)
```

### 6.2 Inspect Generated Files
```bash
# Check phenotypes summary
cat /var/local/CLSA_PheWeb_data/generated_by_pheweb/phenotypes.json

# Check if Manhattan data was generated
ls /var/local/CLSA_PheWeb_data/generated_by_pheweb/manhattan/

# Check QQ plot data
ls /var/local/CLSA_PheWeb_data/generated_by_pheweb/qq/
```

## Step 7: Start the API Server

### 7.1 Launch Backend Server
```bash
# Start the PheWeb API server
pheweb-run
```

The server will start on `http://localhost:9099`

### 7.2 Verify Server is Running
```bash
# Test basic connectivity
curl http://localhost:9099/

# Should return API documentation page
```

## Step 8: Test API Endpoints

### 8.1 Test Phenotypes Endpoint
```bash
# Get all phenotypes
curl http://localhost:9099/phenotypes

# Expected response:
# [{"phenocode": "BLD_nonHDL_COM", "phenostring": "Blood Non-HDL Cholesterol Combined", ...}]
```

### 8.2 Test Variant Endpoints
```bash
# Get stratification list
curl http://localhost:9099/variant/stratification_list

# Get category list  
curl http://localhost:9099/variant/category_list

# Test specific variant (using a variant from your data)
curl "http://localhost:9099/variant/1-769809-A-C/european.male"
```

### 8.3 Test Manhattan Plot Data
```bash
# Get Manhattan plot data for the phenotype
curl http://localhost:9099/manhattan/BLD_nonHDL_COM
```

### 8.4 Test QQ Plot Data
```bash
# Get QQ plot data
curl http://localhost:9099/qq/BLD_nonHDL_COM
```

## Step 9: Advanced Testing

### 9.1 Test with Python Requests
```python
import requests
import json

# Test phenotypes endpoint
response = requests.get('http://localhost:9099/phenotypes')
phenotypes = response.json()
print(f"Found {len(phenotypes)} phenotypes")

# Test specific variant
variant_code = "1-769809-A-C"  # From your sample data
response = requests.get(f'http://localhost:9099/variant/{variant_code}/european.male')
if response.status_code == 200:
    variant_data = response.json()
    print(f"Variant data: {json.dumps(variant_data, indent=2)}")
else:
    print(f"Variant not found: {response.status_code}")
```

### 9.2 Test Autocomplete Functionality
```bash
# If autocomplete was generated, test searching
curl "http://localhost:9099/autocomplete?query=1:769"
```

## Step 10: Troubleshooting

### 10.1 Common Issues

**Issue**: `VariantServiceNotAvailable` error
**Solution**: Check that `BASE_DIR` in config.py points to the correct generated data directory

**Issue**: No data in Manhattan plots
**Solution**: Verify preprocessing completed successfully and check for errors in logs

**Issue**: Import quality filtering removes all variants  
**Solution**: Check `MIN_IMP_QUALITY` setting in config.py (try lowering to 0.1)

### 10.2 Debug Commands
```bash
# Check preprocessing logs
pheweb process --verbose

# Validate phenotype list
python -c "import json; print(json.load(open('pheno-list.json')))"

# Check data directory permissions
ls -la /var/local/CLSA_PheWeb_data/generated_by_pheweb/
```

## Step 11: API Documentation

### 11.1 Access Interactive Documentation
Visit `http://localhost:9099/` in your browser to see the complete API documentation with interactive testing capabilities.

### 11.2 Key Endpoints Summary
- `GET /phenotypes` - List all phenotypes
- `GET /variant/<variant_code>/<stratification>` - Get variant PheWAS data
- `GET /variant/stratification_list` - Available stratifications
- `GET /variant/category_list` - Available categories  
- `GET /manhattan/<phenocode>` - Manhattan plot data
- `GET /qq/<phenocode>` - QQ plot data
- `GET /autocomplete?query=<term>` - Search variants/rsIDs

## Success Criteria

Server starts without errors  
`/phenotypes` returns your BLD_nonHDL_COM phenotype  
Manhattan and QQ endpoints return plot data  
Variant endpoints return association results  
Interactive documentation is accessible

Your PheWeb 2.0 API is now ready for testing and development!
