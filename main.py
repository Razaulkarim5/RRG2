import os
import pandas as pd
from rrg import calculate, plot


# Folders for each frequency data (adjust these paths as needed)
data_folder_daily   = "datasets/cleaned_daily"
data_folder_weekly  = "datasets/cleaned_weekly"
data_folder_monthly = "datasets/cleaned_monthly"

benchmark_ticker = "^GSPC"
tickers = ["AAPL", "AMZN", "AVGO", "BRK-B", "GOOGL",
           "META", "MSFT", "NVDA", "TSLA", "TSM","MCD", "BA"]

def load_and_prepare(folder_path):
    """
    Loads the benchmark (^GSPC) and each ticker’s Close data from the given folder,
    aligns them on common dates, and returns (benchmark_close, ticker_df).
    """
    bench_path = os.path.join(folder_path, f"{benchmark_ticker}.csv")
    if not os.path.exists(bench_path):
        raise FileNotFoundError(f"Missing benchmark file: {bench_path}")
    bench_df = pd.read_csv(bench_path, parse_dates=["Date"], index_col="Date")

    ticker_data = {}
    for tkr in tickers:
        file_path = os.path.join(folder_path, f"{tkr}.csv")
        if not os.path.exists(file_path):
            print(f"Warning: Missing file {file_path}, skipping.")
            continue
        df = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")
        ticker_data[tkr] = df["Close"].ffill()  # forward fill missing values

    ticker_df = pd.DataFrame(ticker_data)
    common_dates = bench_df.index.intersection(ticker_df.index)
    bench_df = bench_df.loc[common_dates]
    ticker_df = ticker_df.loc[common_dates]
    return bench_df["Close"], ticker_df

# --- Load Daily Data ---
bench_daily, tickers_daily = load_and_prepare(data_folder_daily)
rs_daily, rsm_daily = calculate(bench_daily, tickers_daily, window=15)

# --- Load Weekly Data ---
bench_weekly, tickers_weekly = load_and_prepare(data_folder_weekly)
rs_weekly, rsm_weekly = calculate(bench_weekly, tickers_weekly, window=15)

# --- Load Monthly Data ---
bench_monthly, tickers_monthly = load_and_prepare(data_folder_monthly)
rs_monthly, rsm_monthly = calculate(bench_monthly, tickers_monthly, window=15)

# Build dictionaries to pass to rrg.py.
freq_rs = {
    "Daily": rs_daily,
    "Weekly": rs_weekly,
    "Monthly": rs_monthly
}
freq_rsm = {
    "Daily": rsm_daily,
    "Weekly": rsm_weekly,
    "Monthly": rsm_monthly
}

# Optional: save or print a message for each frequency
# (You can comment out any lines you don't need.)
out_csv_daily = os.path.join("datasets", "rrg_output_daily.csv")
rs_daily.to_csv(out_csv_daily)
print(f"✅ Daily RRG calculation done. Saved to {out_csv_daily}")

out_csv_weekly = os.path.join("datasets", "rrg_output_weekly.csv")
rs_weekly.to_csv(out_csv_weekly)
print(f"✅ Weekly RRG calculation done. Saved to {out_csv_weekly}")

out_csv_monthly = os.path.join("datasets", "rrg_output_monthly.csv")
rs_monthly.to_csv(out_csv_monthly)
print(f"✅ Monthly RRG calculation done. Saved to {out_csv_monthly}")

# Finally, plot the RRG with the frequency dropdown
plot(freq_rs, freq_rsm, tail=3 , frame=10)


