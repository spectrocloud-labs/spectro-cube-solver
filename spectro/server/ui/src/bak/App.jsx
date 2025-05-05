import { useState, useEffect } from "react";
import "./styles.css"; // Import CSS file

const WS_URL = `${window.location.origin.replace(/^http/, "ws")}/ws/`;


function App() {
  const [image, setImage] = useState(null);
  const [solution, setSolution] = useState("");
  const [currentStepIndex, setCurrentStepIndex] = useState(-1); // Track step index
  const [solutionArray, setSolutionArray] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => console.log("Connected to WebSocket");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "image") {
        setImage(`data:image/jpeg;base64,${data.image_data}`);
      } else if (data.type === "solution") {
        setSolution(data.solution);
        setSolutionArray(data.solution.split("")); // Convert to character array
      } else if (data.type === "command") {
        setCurrentStepIndex(data.step - 1); // ✅ Ensure step value maps correctly to index
      }
    };

    ws.onclose = () => console.log("WebSocket connection closed");

    return () => ws.close();
  }, []);

  return (
    <div className="container">
      
      {/* Section 1: Display Image */}
      <div className="section">
        <h2>Live Image</h2>
        <div className="image-container">
          {image ? (
            <img src={image} alt="Live Feed" className="image" />
          ) : (
            <p>Waiting for image...</p>
          )}
        </div>
      </div>

      {/* Section 2: Display Full Solution */}
      <div className="section">
        <h2>Solution</h2>
        <p className="solution">{solution || "Waiting for solution..."}</p>
      </div>

      {/* Section 3: Highlight Current Character Based on Step */}
      <div className="section">
        <h2>Current Command</h2>
        <div className="command-container">
          {solutionArray.map((char, index) => (
            <span
              key={index}
              className={index === currentStepIndex ? "highlight-red" : ""}
            >
              {char}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
