import Layout from "./layout/Layout.tsx"
import { useTelemetry } from "./hooks/useTelemetry.ts";

function App() {
  
  useTelemetry();

  return (
    <Layout />
  );
}

export default App;
