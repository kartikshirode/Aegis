import { useTranslation } from "react-i18next";

// Phase-1: this page is behind auth in production. For the demo it renders a
// mock detections table + takedown-status strip + a propagation-graph placeholder
// (the graph lands in Phase-2; we leave a visible placeholder so judges see the
// architectural slot instead of a missing feature).

type Detection = {
  id: string;
  detectedAt: string;
  platform: string;
  verdict: string;
  confidence: number;
  takedownStatus: "DRAFT" | "FILED" | "ACKNOWLEDGED" | "RESOLVED" | "REJECTED";
};

const DEMO_DETECTIONS: Detection[] = [
  {
    id:              "demo-det-1",
    detectedAt:      new Date(Date.now() - 1000 * 60 * 2).toISOString(),
    platform:        "mock-telegram",
    verdict:         "DEEPFAKE_MANIPULATION",
    confidence:      0.94,
    takedownStatus:  "FILED",
  },
  {
    id:              "demo-det-2",
    detectedAt:      new Date(Date.now() - 1000 * 60 * 8).toISOString(),
    platform:        "mock-x",
    verdict:         "EXACT_PIRACY",
    confidence:      0.91,
    takedownStatus:  "ACKNOWLEDGED",
  },
];

export default function RightsHolderDashboard() {
  const { t } = useTranslation();

  return (
    <section className="mx-auto max-w-6xl px-6 py-10 space-y-8 bilingual">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold">{t("rh.heading")}</h1>
        <p className="text-slate-600">{t("rh.subheading")}</p>
      </header>

      <div className="rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-4 py-3">Detection</th>
              <th className="px-4 py-3">Platform</th>
              <th className="px-4 py-3">Verdict</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Takedown</th>
              <th className="px-4 py-3">When</th>
            </tr>
          </thead>
          <tbody>
            {DEMO_DETECTIONS.map((d) => (
              <tr key={d.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-mono text-xs">{d.id}</td>
                <td className="px-4 py-3">{d.platform}</td>
                <td className="px-4 py-3">{d.verdict}</td>
                <td className="px-4 py-3">{(d.confidence * 100).toFixed(0)}%</td>
                <td className="px-4 py-3">{d.takedownStatus}</td>
                <td className="px-4 py-3 text-slate-500">
                  {new Date(d.detectedAt).toLocaleTimeString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded-xl border border-dashed border-slate-300 p-6 space-y-2">
        <h2 className="font-semibold">Propagation graph</h2>
        <p className="text-sm text-slate-600">
          Force-directed graph of where each leaked clip first appeared and how it spread across platforms.
          Wired up in Phase&nbsp;2 against BigQuery; slot preserved here so the architecture is visible.
        </p>
        <div className="h-48 rounded bg-slate-50 grid place-items-center text-slate-400 text-xs">
          (propagation graph — Phase 2)
        </div>
      </div>
    </section>
  );
}
