import React, { useState, useEffect } from "react";

function App() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    // Use relative URL or environment variable for API
    // This works better with Docker networking
    const apiUrl = process.env.REACT_APP_API_URL || "/api";
    
    setLoading(true);
    fetch(`${apiUrl}/`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        setMessage(data.message);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching data:", err);
        setError("Failed to connect to backend service");
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ margin: "2rem", fontFamily: "Arial, sans-serif" }}>
      <h1>FinOps MVP Frontend</h1>
      
      {loading ? (
        <p>Loading...</p>
      ) : error ? (
        <div style={{ color: "red" }}>
          <p>{error}</p>
          <p>Please make sure the backend service is running.</p>
        </div>
      ) : (
        <div>
          <p>Backend says: <strong>{message}</strong></p>
          <p>Connection successful!</p>
        </div>
      )}
    </div>
  );
}

export default App;