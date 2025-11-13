import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // POST request to FastAPI backend
    fetch("http://127.0.0.1:8001/api/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tickers: ["AAPL", "MSFT", "GOOG", "AMZN"],
        mode: "max_sharpe",
        allowShort: false,
        historyYears: 5
      })
    })
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching data:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Portfolio Optimizer</h1>
        {loading ? (
          <p>Loading...</p>
        ) : data ? (
          <pre style={{ textAlign: "left", maxHeight: "400px", overflowY: "auto" }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        ) : (
          <p>No data returned.</p>
        )}
      </header>
    </div>
  );
}

export default App;

//uvicorn version2:app --reload --host 127.0.0.1 --port 8000
