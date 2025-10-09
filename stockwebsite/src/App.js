import React, { useEffect, useState } from "react";

function App() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    // Fetch from backend
    fetch("http://localhost:8000/api/hello")
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => console.error("Error fetching backend:", err));
  }, []);

  return (
    <div style={{ padding: "2rem" }}>
      <h1>React + FastAPI Test</h1>
      <p>Backend says: {message}</p>
    </div>
  );
}

export default App;


