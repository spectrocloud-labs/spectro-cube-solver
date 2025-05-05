import { useState, useEffect } from "react";
import "./styles.css"; // Import CSS file

const WS_URL = `${window.location.origin.replace(/^http/, "ws")}/ws/`;

function App() {
  const [image, setImage] = useState(null);
  const [solution, setSolution] = useState("");
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [solutionArray, setSolutionArray] = useState([]);
  const [cubeFaces, setCubeFaces] = useState({});
  const [robotState, setRobotState] = useState("");

  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => console.log("Connected to WebSocket:", WS_URL);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "image") {
        setImage(`data:image/jpeg;base64,${data.image_data}`);
      } else if (data.type === "solution") {
        setSolution(data.solution);
        setSolutionArray(data.solution.split(""));
        setCurrentStepIndex(-1);
      } else if (data.type === "command") {
        setCurrentStepIndex(data.step - 1);
      } else if (data.type === "face") {
        const { side, image_data } = data;
        setCubeFaces((prev) => ({ ...prev, [side]: `data:image/jpeg;base64,${image_data}` }));
      } else if (data.type === "status") {
        setRobotState(data.robot_state);

        if (data.robot_state === "Scrambling") {
          setImage(null);
          setSolution("");
          setSolutionArray([]);
          setCurrentStepIndex(-1);
          setCubeFaces({});
        } 
      }
    };

    ws.onclose = () => console.log("WebSocket connection closed");

    return () => ws.close();
  }, []);
return (
  <div className="container">
    {/* ✅ Logo & Side Tray */}
    <div className="logo-container">
      <img src="/spectrocloud-logo.png" alt="Robot Control Logo" className="logo" />
    </div>

    <div className="side-tray">
      {[1, 2, 3, 4, 5, 6].map((side) => (
        <div key={side} className="face-image-container">
          {cubeFaces[side] ? (
            <img src={cubeFaces[side]} alt={`Side ${side}`} className="face-image" />
          ) : (
            <p className="placeholder">Side {side}</p>
          )}
        </div>
      ))}
    </div>

    {/* ✅ Main Content */}
    <div className="main-content">
      <div className="section">
        <h2>Scanned Cube Collage</h2>
        <div className="image-container">
          {image ? <img src={image} alt="Live Feed" className="image" /> : <p>Waiting for image...</p>}
        </div>
      </div>

                  <div className="solution-container">
                <div className="section solution-box">
                    <h2>Solution</h2>
                    <p className="solution">{solution || "Waiting for solution..."}</p>
                </div>

            </div>
	
      <div className="section current-command-box">
        <h2>Current Command</h2>
        <div className="command-container">
          {solutionArray.map((char, index) => (
            <span key={index} className={index === currentStepIndex ? "highlight-red" : ""}>
              {char}
            </span>
          ))}
        </div>
      </div>
    </div>
     <div className="info-column">
      <div className="section status-box">
       <h2>Robot Status</h2>
           <p className={`robot-status ${robotState}`}>{robotState || "Waiting for status..."}</p>
      </div>
      <div className="section legend-box">
        <h2>Command Legend</h2>
           <ul className="legend">
               <li><strong>F</strong> - Flip</li>
               <li><strong>S</strong> - Spin</li>
               <li><strong>R</strong> - Rotate Layer</li>
           </ul>
       </div>
    </div>
  </div>
);

}

export default App;

