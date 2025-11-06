# Quantitative Stock Analyzer

![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A command-line Python script for performing quantitative-driven fundamental analysis on a given stock ticker, featuring automated data fetching, Piotroski F-Score, CAPM, and a data-driven DCF valuation.

---

## 📖 Table of Contents

- [About The Project](#about-the-project)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Limitations & Disclaimers](#limitations--disclaimers)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## 📌 About The Project

This script automates the process of quantitative fundamental analysis. Instead of relying on subjective "assumptions" for valuation, this tool calculates key inputs (like the discount rate and growth rate) based on historical financial data and established financial models.

It is built to be a single, easy-to-run script that outputs a comprehensive summary of a company's financial health and intrinsic value.

## ✨ Key Features

* **Financial Statement Fetching:** Pulls annual Income Statements, Balance Sheets, and Cash Flow Statements from Alpha Vantage.
* **Key Ratio Analysis:** Calculates standard metrics like P/E, P/B, ROE, and Debt-to-Equity.
* **Piotroski F-Score:** Implements the 9-point Piotroski F-Score model to grade a company's financial strength (Profitability, Leverage, and Operating Efficiency).
* **Historical Growth (CAGR):** Automatically calculates the 5-year Compound Annual Growth Rate (CAGR) for revenue and net income.
* **CAPM Discount Rate:** Calculates the Cost of Equity using the Capital Asset Pricing Model (CAPM) to determine a data-driven discount rate (WACC proxy).
* **Data-Driven DCF Valuation:** Runs a 5-year Discounted Cash Flow (DCF) model where the **growth rate** and **discount rate** are derived from the script's
