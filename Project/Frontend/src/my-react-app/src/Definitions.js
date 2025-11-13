import React, { useState } from "react";

function Term({ term, definition, example }) {
  const [open, setOpen] = useState(false);

  return (
    <div style={styles.termContainer}>
      <div style={styles.termHeader} onClick={() => setOpen(!open)}>
        <strong>{term}</strong>
        <span style={styles.toggle}>{open ? "−" : "+"}</span>
      </div>
      {open && (
        <div style={styles.definition}>
          <div>{definition}</div>
          {example && <div style={styles.example}>Example: {example}</div>}
        </div>
      )}
    </div>
  );
}

export default function Definitions() {
  const definitions = [
    {
      term: "Sharpe Ratio",
      definition:
        "A measure of risk-adjusted return. Higher Sharpe means more return per unit of risk.",
      example: "A portfolio with a Sharpe of 1.5 is better risk-adjusted than one with 1.0.",
    },
    {
      term: "Volatility",
      definition:
        "A measure of how much a portfolio's return fluctuates. Higher volatility = higher risk.",
      example: "A stock moving ±20% per year is more volatile than one moving ±5%.",
    },
    {
      term: "Expected Return",
      definition:
        "The average return you would expect from a portfolio based on historical data.",
      example: "If a portfolio averages 8% per year over the past 10 years, that is its expected return.",
    },
    {
      term: "Beta (β)",
      definition:
        "Measures a stock's sensitivity to market movements. β > 1 means more volatile than the market.",
      example: "β = 1.2 means if the market goes up 10%, the stock may go up ~12%.",
    },
    {
      term: "CAPM Expected Return",
      definition:
        "Expected return based on the Capital Asset Pricing Model: risk-free rate + β*(market return - risk-free rate).",
      example: "If Rf = 3%, Rm = 8%, β = 1.2 → CAPM return = 3 + 1.2*(8-3) = 9%.",
    },
    {
      term: "CAGR (approx)",
      definition:
        "Compound Annual Growth Rate. Average annual growth of an investment over time.",
      example: "An investment that grows from $100 → $161 in 5 years has CAGR ≈ 10%.",
    },
    {
      term: "Max Sharpe",
      definition:
        "Optimizes the portfolio to maximize the Sharpe ratio (best risk-adjusted return).",
    },
    {
      term: "Min Variance",
      definition:
        "Optimizes the portfolio to minimize overall portfolio variance (risk).",
    },
    {
      term: "Target Return",
      definition:
        "Optimizes portfolio weights to reach a specific expected return while controlling risk.",
    },
    {
      term: "Rm",
      definition:
        "Expected market return (e.g., S&P 500 long-term mean).",
    },
    {
      term: "Rf",
      definition:
        "Risk-free rate, typically long-term government bond yield.",
    },
  ];

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1>Definitions</h1>
        <div style={{ color: "#6b7280" }}>
          Click a term to expand its explanation
        </div>
      </header>

      <main style={styles.main}>
        {definitions.map((d) => (
          <Term key={d.term} {...d} />
        ))}
      </main>
    </div>
  );
}

// ---------- styles ----------
const styles = {
  page: {
    minHeight: "100vh",
    background: "#f6f7fb",
    color: "#111827",
    fontFamily:
      '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,"Apple Color Emoji","Segoe UI Emoji"',
    paddingBottom: 32,
  },
  header: {
    maxWidth: 1100,
    margin: "0 auto",
    padding: "24px 16px",
  },
  main: {
    display: "grid",
    gap: 16,
    maxWidth: 1100,
    margin: "0 auto",
    padding: "0 16px",
  },
  termContainer: {
    background: "white",
    border: "1px solid #e5e7eb",
    borderRadius: 12,
    padding: 12,
    cursor: "pointer",
    boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
  },
  termHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: 15,
  },
  toggle: {
    fontWeight: "bold",
    fontSize: 18,
    lineHeight: 1,
  },
  definition: {
    marginTop: 8,
    fontSize: 14,
    color: "#374151",
  },
  example: {
    marginTop: 4,
    fontStyle: "italic",
    color: "#6b7280",
  },
};
