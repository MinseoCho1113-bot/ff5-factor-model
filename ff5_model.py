# Fama-French 5-Factor Model: S&P 500 (SPY)

import io
import zipfile
import urllib.request

import pandas as pd
import yfinance as yf
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson
import matplotlib.pyplot as plt


# Step 1: Download the 5-factor data
#         from Kenneth French's Data Library

URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_5_Factors_2x3_CSV.zip"
)

# Download the zip file and read the CSV inside it as text
req = urllib.request.Request(
    URL,
    headers={"User-Agent": "Mozilla/5.0"},
)
raw = urllib.request.urlopen(req).read()
z = zipfile.ZipFile(io.BytesIO(raw))
text = z.read(z.namelist()[0]).decode("utf-8", errors="ignore")

# The file mixes description text, monthly data, and annual data.
# Keep only rows whose first column is a 6-digit date
# (e.g. 201001 = Jan 2010).
rows = []
for line in text.splitlines():
    parts = [p.strip() for p in line.split(",")]
    if len(parts) == 7 and parts[0].isdigit() and len(parts[0]) == 6:
        rows.append(parts)

# Build a table (DataFrame)
cols = ["date", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]
factors = pd.DataFrame(rows, columns=cols)
factors["date"] = pd.to_datetime(
    factors["date"],
    format="%Y%m",
).dt.to_period("M")
factors = factors.set_index("date").astype(float)  # in percent (%)

print("Factor data (last 5 months):")
print(factors.tail())
print(f"Total: {len(factors)} months")

# ---------------------------------------------
# Step 2: Download SPY prices
#         and compute monthly returns
# ---------------------------------------------
TICKER = "SPY"          # S&P 500 ETF
START = "2010-01-01"    # start date of the analysis

# Download daily prices
# (auto_adjust=True: adjusted for dividends and splits)
prices = yf.download(
    TICKER,
    start=START,
    auto_adjust=True,
    progress=False,
)
close = prices["Close"].squeeze()

# Last price of each month -> monthly return in percent
monthly_close = close.groupby(close.index.to_period("M")).last()
spy_ret = monthly_close.pct_change().dropna() * 100
spy_ret.name = "SPY"

print("\nSPY monthly returns (last 5 months):")
print(spy_ret.tail())
print(f"Total: {len(spy_ret)} months")

# 
# Step 3: Merge the two datasets by month

df = factors.join(spy_ret, how="inner")

# Excess return = SPY return - risk-free rate
df["SPY_excess"] = df["SPY"] - df["RF"]

start_month = df.index[0]
end_month = df.index[-1]
print(f"\nMerged: {start_month} to {end_month}")
print(f"Number of months: {len(df)}")


# Step 4: Run the 5-factor regression (OLS)

factor_cols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
X = sm.add_constant(df[factor_cols])   # const = alpha
y = df["SPY_excess"]

model = sm.OLS(y, X).fit()
print(model.summary())


# Step 5: Check residual autocorrelation

resid = model.resid   # monthly errors (actual - predicted)

# (1) Durbin-Watson: compute it by hand, then compare with statsmodels
dw_manual = (resid.diff() ** 2).sum() / (resid ** 2).sum()
dw_lib = durbin_watson(resid)
print(f"\nDurbin-Watson (manual):      {dw_manual:.3f}")
print(f"Durbin-Watson (statsmodels): {dw_lib:.3f}")

# (2) Plot the residuals
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Left: residuals over time
dates = resid.index.to_timestamp()
axes[0].plot(dates, resid.values, linewidth=1)
axes[0].axhline(0, color="gray", linestyle="--")
axes[0].set_title("Residuals over time")
axes[0].set_xlabel("Month")
axes[0].set_ylabel("Residual (%)")

# Right: this month's residual vs last month's residual
axes[1].scatter(resid.shift(1), resid, s=12)
axes[1].axhline(0, color="gray", linestyle="--")
axes[1].axvline(0, color="gray", linestyle="--")
axes[1].set_title("This month vs last month")
axes[1].set_xlabel("Residual last month (%)")
axes[1].set_ylabel("Residual this month (%)")

plt.tight_layout()
plt.savefig("residuals.png", dpi=150)
print("Saved: residuals.png")

