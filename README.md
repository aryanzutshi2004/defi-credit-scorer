# 🏦 DeFi Credit Scoring using Aave V2 Transaction Data

This project develops a **credit scoring pipeline** using DeFi transaction histories from the **Aave V2 protocol on the Polygon blockchain**. It parses and transforms raw transaction data into meaningful features, builds a machine learning model to predict a user's credit score quantile, and serves the model using a FastAPI web application.

---

## 📌 Objective

Traditional credit scoring models rely on centralized financial data. However, with the rise of DeFi, it's essential to develop on-chain alternatives. This project:
- Parses user-level transaction data from Aave V2
- Engineers meaningful financial behavior features
- Models credit score quantiles using machine learning
- Deploys the model as an API for real-time inference

---

## 📥 Data Description

The input data is a list of JSON transaction records. Each record describes a user's interaction with Aave, such as deposits, borrows, or repayments.  

### Sample JSON Entry:
```json
{
  "userWallet": "0x123...abcd",
  "action": "deposit",
  "timestamp": 1629178166,
  "actionData": {
    "amount": "2000000000",
    "assetPriceUSD": "0.99",
    "assetSymbol": "USDC"
  }
}
