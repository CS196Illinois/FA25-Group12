// Optimizer.js
import React, { useState } from "react";
import axios from "axios";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const API = "http://localhost:8000/api/optimize"; // backend URL
const COLORS = [
  "#2563eb",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#14b8a6",
  "#f43f5e",
  "#22c55e",
  "#eab308",
  "#0ea5e9",
];

function Section({ title, children }) {
  return (
    <div style={styles.card}>
      <div style={styles.cardTitle}>{title}</div>
      {children}
    </div>
  );
}

export default function Optimizer() {
  // ---- form state
  const [tickers, setTickers] = useState(["AAPL", "MSFT", "NVDA"]);
  const [newTicker, setNewTicker] = useState("");
  const [mode, setMode] = useState("max_sharpe");
  const [targetReturn, setTargetReturn] = useState("0.12");
  const [years, setYears] = useState(5);

  // ---- result state
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState(null);

  const addTicker = () => {
    const t = newTicker.trim().toUpperCase();
    if (t && !tickers.includes(t)) setTickers([...tickers, t]);
    setNewTicker("");
  };
  const removeTicker = (t) => setTickers((xs) => xs.filter((x) => x !== t));

  const runOptimize = async () => {
    setErr("");
    setLoading(true);
    setRes(null);
    try {
      const payload = {
        tickers,
        mode,
        targetReturn: mode === "target_return" ? Number(targetReturn) : null,
        historyYears: Number(years),
      };
      const r = await axios.post(API, payload, { timeout: 120000 });
      setRes(r.data);
    } catch (e) {
      console.error(e);
      setErr(
        "Optimization failed. Ensure the backend is running and tickers are valid."
      );
    } finally {
      setLoading(false);
    }
  };

  const pieData = res
    ? Object.entries(res.weights || {}).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={{ margin: 0 }}>Portfolio Optimizer</h1>
        <div style={{ color: "#6b7280" }}>
          CAPM + Mean-Variance (Max Sharpe / Min Variance / Target Return)
        </div>
      </header>

      <main style={styles.main}>
        {/* Left: Inputs */}
        <Section title="Inputs">
          <div style={{ display: "grid", gap: 12 }}>
            {/* Ticker entry */}
            <div>
              <div style={styles.label}>Add ticker</div>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  value={newTicker}
                  onChange={(e) => setNewTicker(e.target.value)}
                  placeholder="e.g., AMZN"
                  style={styles.input}
                />
                <button onClick={addTicker} style={styles.primaryBtn}>
                  Add
                </button>
              </div>
            </div>

            {/* Current tickers */}
            <div>
              <div style={styles.label}>Selected tickers</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {tickers.map((t) => (
                  <span key={t} style={styles.chip}>
                    {t}
                    <button
                      onClick={() => removeTicker(t)}
                      style={styles.chipX}
                      title="Remove"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Mode + target */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <div>
                <div style={styles.label}>Mode</div>
                <select
                  value={mode}
                  onChange={(e) => setMode(e.target.value)}
                  style={styles.input}
                >
                  <option value="max_sharpe">Max Sharpe</option>
                  <option value="min_variance">Min Variance</option>
                  <option value="target_return">Target Return</option>
                </select>
              </div>
              <div>
                <div style={styles.label}>Target Return (decimal)</div>
                <input
                  type="number"
                  step="0.01"
                  disabled={mode !== "target_return"}
                  value={targetReturn}
                  onChange={(e) => setTargetReturn(e.target.value)}
                  style={{ ...styles.input, opacity: mode === "target_return" ? 1 : 0.6 }}
                />
              </div>
            </div>

            {/* Years + shorting */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8 }}>
              <div>
                <div style={styles.label}>History (years)</div>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={years}
                  onChange={(e) => setYears(e.target.value)}
                  style={styles.input}
                />
              </div>
            </div>

            <button onClick={runOptimize} style={styles.primaryBtn} disabled={loading}>
              {loading ? "Optimizing..." : "Run Optimizer"}
            </button>

            {err && <div style={styles.error}>{err}</div>}
          </div>
        </Section>

        {/* Right: Results */}
        <div style={{ display: "grid", gap: 16 }}>
          <Section title="Weights">
            {res && pieData.length > 0 ? (
              <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 16 }}>
                {/* Table */}
                <div style={{ overflowX: "auto" }}>
                  <table style={styles.table}>
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Weight</th>
                        <th>β</th>
                        <th>CAPM Exp.</th>
                        <th>CAGR (approx)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {res.usedTickers.map((t) => {
                        const w = res.weights[t] ?? 0;
                        const info = (res.perStock && res.perStock[t]) || {};
                        const beta = info.beta;
                        const capm = info.expectedCAPM;
                        const cagr = info.cagrApprox;
                        return (
                          <tr key={t}>
                            <td>{t}</td>
                            <td>{(w * 100).toFixed(2)}%</td>
                            <td>{Number.isFinite(beta) ? beta.toFixed(3) : "—"}</td>
                            <td>{Number.isFinite(capm) ? (capm * 100).toFixed(2) + "%" : "—"}</td>
                            <td>{Number.isFinite(cagr) ? (cagr * 100).toFixed(2) + "%" : "—"}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Pie */}
                <div style={{ width: 320, height: 260 }}>
                  <PieChart width={320} height={260}>
                    <Pie
                      data={pieData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                    >
                      {pieData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => (v * 100).toFixed(2) + "%"} />
                    <Legend />
                  </PieChart>
                </div>
              </div>
            ) : (
              <div style={{ color: "#6b7280" }}>No results yet.</div>
            )}
          </Section>

          <Section title="Portfolio Stats (annualized)">
            {res ? (
              <div style={{ display: "grid", gap: 8 }}>
                <div style={styles.kv}>
                  <div>Expected Return</div>
                  <div>{(res.stats.expected_return * 100).toFixed(2)}%</div>
                </div>
                <div style={styles.kv}>
                  <div>Volatility</div>
                  <div>{(res.stats.volatility * 100).toFixed(2)}%</div>
                </div>
                <div style={styles.kv}>
                  <div>Sharpe (Rf {(res.market.Rf * 100).toFixed(2)}%)</div>
                  <div>{Number(res.stats.sharpe).toFixed(3)}</div>
                </div>

                <hr style={{ border: "none", borderTop: "1px solid #e5e7eb" }} />

                <div style={{ color: "#6b7280" }}>Equal-Weight Baseline</div>
                <div style={styles.kv}>
                  <div>Expected Return</div>
                  <div>{(res.baseline.expected_return * 100).toFixed(2)}%</div>
                </div>
                <div style={styles.kv}>
                  <div>Volatility</div>
                  <div>{(res.baseline.volatility * 100).toFixed(2)}%</div>
                </div>
                <div style={styles.kv}>
                  <div>Sharpe</div>
                  <div>{Number(res.baseline.sharpe).toFixed(3)}</div>
                </div>
              </div>
            ) : (
              <div style={{ color: "#6b7280" }}>No stats yet.</div>
            )}
          </Section>

          <Section title="Market Snapshot">
            {res ? (
              <div style={{ display: "flex", gap: 24 }}>
                <div>Rm (S&P 500 long-run mean): {(res.market.Rm * 100).toFixed(2)}%</div>
                <div>Rf (10Y): {(res.market.Rf * 100).toFixed(2)}%</div>
              </div>
            ) : (
              <div style={{ color: "#6b7280" }}>—</div>
            )}
          </Section>
        </div>
      </main>
    </div>
  );
}

// ---------- simple styles ----------
const styles = {
  page: {
    minHeight: "100vh",
    background: "#f6f7fb",
    color: "#111827",
    fontFamily:
      '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,"Apple Color Emoji","Segoe UI Emoji"',
  },
  header: {
    maxWidth: 1100,
    margin: "0 auto",
    padding: "24px 16px",
  },
  main: {
    display: "grid",
    gridTemplateColumns: "360px 1fr",
    gap: 16,
    maxWidth: 1100,
    margin: "0 auto",
    padding: "0 16px 32px",
  },
  card: {
    background: "white",
    border: "1px solid #e5e7eb",
    borderRadius: 16,
    padding: 16,
    boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
  },
  cardTitle: {
    fontSize: 13,
    color: "#6b7280",
    fontWeight: 600,
    marginBottom: 8,
  },
  label: { fontSize: 12, color: "#6b7280", marginBottom: 6 },
  input: {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 12,
    border: "1px solid #d1d5db",
    background: "white",
  },
  primaryBtn: {
    padding: "10px 12px",
    borderRadius: 12,
    border: "1px solid #111827",
    background: "#111827",
    color: "white",
    cursor: "pointer",
  },
  chip: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "6px 10px",
    borderRadius: 999,
    background: "#e5e7eb",
    fontSize: 13,
  },
  chipX: {
    background: "transparent",
    border: "none",
    cursor: "pointer",
    color: "#6b7280",
    fontSize: 16,
    lineHeight: 1,
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: 14,
  },
  kv: {
    display: "flex",
    justifyContent: "space-between",
    padding: "6px 0",
  },
  error: {
    color: "#b91c1c",
    background: "#fee2e2",
    border: "1px solid #fecaca",
    padding: "8px 10px",
    borderRadius: 10,
  },
};
