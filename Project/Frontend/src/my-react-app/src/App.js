// App.js
import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Optimizer from "./Optimizer";
import Definitions from "./Definitions";

const navStyle = {
  display: "flex",
  gap: 12,
  alignItems: "center",
  padding: 16,
  borderBottom: "1px solid #e5e7eb",
  background: "#ffffff",
};

const linkStyle = {
  textDecoration: "none",
  color: "#111827",
  padding: "8px 12px",
  borderRadius: 8,
};

const activeLinkStyle = {
  ...linkStyle,
  background: "#111827",
  color: "white",
};

export default function App() {
  return (
    <Router>
      <div style={navStyle}>
        <Link to="/" style={linkStyle}>
          Optimizer
        </Link>
        <Link to="/definitions" style={linkStyle}>
          Definitions
        </Link>
        <div style={{ marginLeft: "auto", color: "#6b7280", fontSize: 14 }}>
          Portfolio Optimizer — CAPM + Mean-Variance
        </div>
      </div>

      <Routes>
        <Route path="/" element={<Optimizer />} />
        <Route path="/definitions" element={<Definitions />} />
      </Routes>
    </Router>
  );
}
