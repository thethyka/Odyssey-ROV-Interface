import { useState, useEffect } from 'react';

function App() {
  const [msg, setMsg] = useState("(loading...)");

  useEffect(() => {
    fetch("http://localhost:8000/hello")
      .then((res) => res.json())
      .then((data) => setMsg(data.message))
      .catch((err) => setMsg("Error: " + err.message));
  }, []);

  return (
    <main>
      <section>
      <p>{msg}</p>  
      </section>      
    </main>
  );
}

export default App;
