import pandas as pd
import json
from joblib import load
import numpy as np

#Load trained artifacts
model = load("artifacts/model.joblib")
scaler_dict = load("artifacts/scaler.joblib")
scaler = scaler_dict.get("scaler")
cols_to_scale = scaler_dict.get("columns")
features = load("artifacts/final_col.joblib")

# Asset decimal places
asset_decimals = {
    "USDC": 6,
    "WMATIC": 18,
    "DAI": 18,
    "WBTC": 8,
    "WETH": 18,
    "USDT": 6,
    "WPOL": 18,
    "AAVE": 18
}

def convert_raw_to_token(row):
    if row["asset"] == "":
        return 0.0
    decimals = asset_decimals.get(row["asset"], 18)
    try:
        return int(row["amount_raw"]) / (10 ** decimals)
    except:
        return 0.0

def parse_tx(tx):
    return {
        "wallet": tx.get("userWallet"),
        "action": tx.get("action"),
        "amount_raw": tx.get("actionData", {}).get("amount"),
        "asset": tx.get("actionData", {}).get("assetSymbol"),
        "asset_price_usd": tx.get("actionData", {}).get("assetPriceUSD"),
    }

# Load and parse JSON input
with open("input.json") as f:
    data = json.load(f)

parsed = [parse_tx(tx) for tx in data]
df = pd.DataFrame(parsed)

# Process amounts and tokens
df["amount_raw"] = pd.to_numeric(df["amount_raw"], errors='coerce')
df["asset_price_usd"] = pd.to_numeric(df["asset_price_usd"], errors='coerce')
df["no_token"] = df.apply(convert_raw_to_token, axis=1)
df["asset"] = df["asset"].fillna("")
df["total_price_usd"] = df["asset_price_usd"] * df["no_token"]

#Feature aggregation
user_features = df.groupby("wallet").agg(
    total_deposit_usd=("total_price_usd", lambda x: x[df.loc[x.index, "action"] == "deposit"].sum()),
    total_borrow_usd=("total_price_usd", lambda x: x[df.loc[x.index, "action"] == "borrow"].sum()),
    total_repay_usd=("total_price_usd", lambda x: x[df.loc[x.index, "action"] == "repay"].sum()),
    total_withdraw_usd=("total_price_usd", lambda x: x[df.loc[x.index, "action"] == "redeemunderlying"].sum()),
    count_deposit=("action", lambda x: (x == "deposit").sum()),
    count_borrow=("action", lambda x: (x == "borrow").sum()),
    count_repay=("action", lambda x: (x == "repay").sum()),
    count_withdraw=("action", lambda x: (x == "redeemunderlying").sum()),
    count_liquidation=("action", lambda x: (x == "liquidationcall").sum()),
)

user_features = user_features.reset_index()
user_features["avg_deposit"] = user_features["total_deposit_usd"] / (user_features["count_deposit"] + 1e-6)
user_features["avg_borrow"] = user_features["total_borrow_usd"] / (user_features["count_borrow"] + 1e-6)
user_features["avg_repay"] = user_features["total_repay_usd"] / (user_features["count_repay"] + 1e-6)
user_features["avg_withdraw"] = user_features["total_withdraw_usd"] / (user_features["count_withdraw"] + 1e-6)
user_features["withdraw_to_depo"] = user_features["total_withdraw_usd"] / (user_features["total_deposit_usd"] + 1e-6)
user_features["borrow_to_deposit"] = user_features["total_borrow_usd"] / (user_features["total_deposit_usd"] + 1e-6)
user_features["repay_to_borrow"] = user_features["total_repay_usd"] / (user_features["total_borrow_usd"] + 1e-6)

# Cap ratios with thresholds
thresholds = {
    "withdraw_to_depo": 1365.93,
    "borrow_to_deposit": 0.8691,
    "repay_to_borrow": 1.0042
}
for col in ["withdraw_to_depo", "borrow_to_deposit", "repay_to_borrow"]:
    user_features[col] = user_features[col].clip(upper=thresholds[col])

# Drop unnecessary columns
features_to_drop = [
    "total_deposit_usd", "total_withdraw_usd",
    "total_borrow_usd", "total_repay_usd"
]
df_users = user_features.drop(columns=features_to_drop)

#Extract wallet addresses for output
wallets = df_users["wallet"].copy()
df_users = df_users.drop(columns=["wallet"])

#Scale required features
df_users[cols_to_scale] = scaler.transform(df_users[cols_to_scale])

# Predict probability & calculate score
y_proba = model.predict_proba(df_users)

# You can define score range here (e.g., 100–1000)
quantile_to_score = [i * 100 for i in range(0, 10)]  # [100, 200, ..., 1000]
expected_scores = y_proba @ quantile_to_score

#Final wallet-score output
wallet_scores = pd.DataFrame({
    "wallet": wallets,
    "score": expected_scores
})

# Output results
print(wallet_scores.to_json(orient="records", indent=2))
