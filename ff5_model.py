# Fama-French 5-Factor Model: S&P 500 (SPY)
# Step 1: Download the 5-factor data from Kenneth French's Data Library

import io
import zipfile
import urllib.request

import pandas as pd

# URL of the monthly Fama-French 5-factor data (US, 2x3 sorts)
URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
       "F-F_Research_Data_5_Factors_2x3_CSV.zip")

# 1) Download the zip file and read the CSV inside it as text
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
raw = urllib.request.urlopen(req).read()
z = zipfile.ZipFile(io.BytesIO(raw))
text = z.read(z.namelist()[0]).decode("utf-8", errors="ignore")

# 2) The file mixes description text, monthly data, and annual data.
#    Keep only rows whose first column is a 6-digit date (e.g. 201001 = Jan 2010).
rows = []
for line in text.splitlines():
    parts = [p.strip() for p in line.split(",")]
    if len(parts) == 7 and parts[0].isdigit() and len(parts[0]) == 6:
        rows.append(parts)

# 3) Build a table (DataFrame)
cols = ["date", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]
factors = pd.DataFrame(rows, columns=cols)
factors["date"] = pd.to_datetime(factors["date"], format="%Y%m").dt.to_period("M")
factors = factors.set_index("date").astype(float)   # values are in percent (%)

# 4) Check the result
print("First 5 months:")
print(factors.head())
print("\nLast 5 months:")
print(factors.tail())
print(f"\nTotal: {len(factors)} months")
