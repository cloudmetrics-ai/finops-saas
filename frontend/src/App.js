import React from "react";

function App() {
  const [message, setMessage] = React.useState("");

  React.useEffect(() => {
    fetch("http://localhost:8000/")
      .then(res => res.json())
      .then(data => setMessage(data.message))
      .catch(err => console.error(err));
  }, []);

  return (
    <div style={{ margin: "2rem" }}>
      <h1>FinOps MVP Frontend</h1>
      <p>Backend says: {message}</p>
    </div>
  );
}

export default App;