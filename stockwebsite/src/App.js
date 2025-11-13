import { useEffect, useState } from "react";

function App() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/hello")
      .then(res => res.json())
      .then(data => {
        console.log(data);       // logs: { message: "Hello from backend!!wowoowwow!" }
        setMessage(data.message); // updates state so it shows in <p>
      })
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      <h1>Stockwebsite + Backend this is cool</h1>
      <p>{message}</p>
    </div>
  );
}

export default App;

