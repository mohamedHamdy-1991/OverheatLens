import { HashRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "./AppShell";
import { Home } from "./pages/Home";
import { WeatherLab } from "./pages/WeatherLab";
import { Analyze } from "./pages/Analyze";
import { Validation } from "./pages/Validation";
import { ComingSoon } from "./pages/ComingSoon";

export default function App() {
  return (
    <HashRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/weather" element={<WeatherLab />} />
          <Route path="/validation" element={<Validation />} />
          <Route path="/compare" element={
            <ComingSoon title="Compare" phase="Phase 9" instead={[
              { to: "/weather", label: "Weather Lab" },
              { to: "/validation", label: "Validation" },
            ]} />} />
          <Route path="/atlas" element={
            <ComingSoon title="Archetype Atlas" phase="Phase 14" instead={[
              { to: "/analyze", label: "Analyze" },
            ]} />} />
          <Route path="/comfort" element={
            <ComingSoon title="Comfort Lab" phase="Phase 12" instead={[
              { to: "/analyze", label: "Analyze" },
            ]} />} />
          <Route path="/mitigation" element={
            <ComingSoon title="Mitigation Lab" phase="Phase 13" instead={[
              { to: "/analyze", label: "Analyze" },
            ]} />} />
          <Route path="/methods" element={
            <ComingSoon title="Methods" phase="Phase 8 (docs)" instead={[
              { to: "/validation", label: "Validation" },
            ]} />} />
          <Route path="/docs" element={
            <ComingSoon title="Docs" phase="Phase 8 (docs)" instead={[
              { to: "/validation", label: "Validation" },
            ]} />} />
          <Route path="/about" element={
            <ComingSoon title="About" phase="Phase 8 (docs)" instead={[
              { to: "/validation", label: "Validation" },
            ]} />} />
        </Routes>
      </AppShell>
    </HashRouter>
  );
}
