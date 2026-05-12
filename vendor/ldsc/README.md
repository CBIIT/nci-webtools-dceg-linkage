# Installing LDSC (Python 3.9+ Branch)
 
This guide covers the installation of the `ldsc39` branch from the CBIIT repository.
 
## 1. Prerequisites
 
Ensure you have the following installed on your system:
 
- git
- Python 3.9 or higher
- conda

 
## 2. Clone the Repository
 
Clone the specific branch (`ldsc39`) from the CBIIT GitHub repository:
 
```
git clone -b ldsc39 https://github.com/CBIIT/ldsc.git
cd ldsc
```
 
## 3. Create a Virtual Environment
 
It is highly recommended to use a dedicated environment to avoid dependency conflicts.
 
### Using Conda (Recommended):
 
```
conda create --name ldsc39 python=3.9
conda activate ldsc39
```
 
## 4. Install Dependencies
 
Install the required Python packages directly from the `requirements.txt` file provided in the repo:
 
```
pip install -r requirements.txt
pip install numpy
pip install bitarray
pip install pandas
pip install scipy
```
 
## 5. Verify Installation
 
Run the help command to ensure the script executes correctly:
 
```
python ldsc.py -h
```
 
## 6. Download Reference Data
 
LDSC requires reference LD scores and HapMap3 SNP lists to run. If you are not using the LDscore cloud web tool and are running this locally, you must download these files:
 
```
# Example: Download BBJ_HDLC22 LD Scores (approx 5.4MB)
wget https://ldlink.nih.gov/LDlinkRestWeb/copy_and_download/BBJ_HDLC22.txt
# munge sumstats
python munge_sumstats.py --sumstats BBJ_HDLC22.txt --out BBJ_HDLC22
# manually download ref EAS data from 1000 genomes and uncompress, move to folder with ldsc.py script
https://drive.google.com/file/d/1BtpWx02ON33KfjyCFSdmoWYlMZWImh2f/view
```
 
## 7. Basic Usage Example
 
Once installed, you can run a basic heritability analysis:
 
```
python ldsc.py \
    --h2 BBJ_HDLC22.sumstats.gz \
    --ref-ld-chr eas_ldscores/ \
    --w-ld-chr eas_ldscores/ \
    --out your_analysis_results
```
 
Technical Note: If you prefer not to manage these local installations and reference files, the LDscore web tool (integrated into LDlink) provides results through a browser without requiring any local setup.
 
## Docker Installation (Alternative)
 
From the project root directory (where the dockerfile is located):
 
Clone the Repository
 
**1. Clone the specific branch (`ldsc39`) from the CBIIT GitHub repository and build the image:**
 
```bash
git clone -b ldsc39 https://github.com/CBIIT/ldsc.git
cd ldsc
docker build -t ldsc39 .
```
 
**2. Run the container:**
 
```bash
docker run -d -it --name ldsc39_container -p 5000:5000 ldsc39
```
 
**3. Access the API:**
 
```bash
curl http://localhost:5000/ldscore
```
 
**Optional - Run a test inside the container:**
 
```
docker exec -it ldsc39_container bash
# Example: Download BBJ_HDLC22 LD Scores (approx 5.4MB)
wget https://ldlink.nih.gov/LDlinkRestWeb/copy_and_download/BBJ_HDLC22.txt
# munge sumstats
python munge_sumstats.py --sumstats BBJ_HDLC22.txt --out BBJ_HDLC22
# manually download ref EAS data from 1000 genomes and uncompress, move to folder with ldsc.py script
https://drive.google.com/file/d/1BtpWx02ON33KfjyCFSdmoWYlMZWImh2f/view
python ldsc.py --bfile 22 --l2 --ld-wind-cm 1 --out 22
```