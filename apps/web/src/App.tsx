import { HashRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "./AppShell";
import { Home } from "./pages/Home";
import { WeatherLab } from "./pages/WeatherLab";
import { Analyze } from "./pages/Analyze";
import { Validation } from "./pages/Validation";
import { Mitigation } from "./pages/Mitigation";
import { ComfortLab } from "./pages/ComfortLab";
import { Compare } from "./pages/Compare";
import { Atlas } from "./pages/Atlas";
import { Runs } from "./pages/Runs";
import { Scenarios } from "./pages/Scenarios";
import { Methods, Docs, About } from "./pages/Info";

export default function App() {
  return (
    <HashRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/weather" element={<WeatherLab />} />
          <Route path="/validation" element={<Validation />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/atlas" element={<Atlas />} />
          <Route path="/comfort" element={<ComfortLab />} />
          <Route path="/mitigation" element={<Mitigation />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/scenarios" element={<Scenarios />} />
          <Route path="/methods" element={<Methods />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </AppShell>
    </HashRouter>
  );
}
