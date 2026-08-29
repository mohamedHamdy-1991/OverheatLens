import { Link } from "react-router-dom";

/* Honest placeholder for surfaces not built yet — never a fake UI (master-prompt
 * phase protocol). Names what exists and where to go instead. */
export function ComingSoon({ title, phase, instead }: { title: string; phase: string; instead: { to: string; label: string }[] }) {
  return (
    <>
      <h1 className="page-title">{title}</h1>
      <p className="page-intro">
        This surface is scheduled for {phase} of the build plan. It is intentionally not
        faked: OverheatLens never shows placeholder science. What exists today:
      </p>
      <div className="table-wrap" style={{ marginTop: 20, maxWidth: 720 }}>
        <table className="data">
          <tbody>
            {instead.map((i) => (
              <tr key={i.to}>
                <td style={{ width: 240 }}><Link to={i.to} style={{ fontWeight: 600 }}>{i.label} →</Link></td>
                <td style={{ color: "var(--muted-ink)" }}><Living description={i.to} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Living({ description }: { description: string }) {
  const map: Record<string, string> = {
    "/analyze": "Run the full pipeline: readiness checks, an EnergyPlus simulation and a versioned standards evaluation.",
    "/weather": "Quality-check any EPW in the local library and read its climate.",
    "/validation": "Read the live validation matrix with every recorded PASS and its evidence.",
    "/": "Start from the overview with the live thermal year.",
  };
  return <>{map[description] ?? ""}</>;
}
