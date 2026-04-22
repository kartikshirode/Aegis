import { useTranslation, Trans } from "react-i18next";
import { Link } from "react-router-dom";
import { AlertTriangle, ShieldCheck } from "lucide-react";

import BilingualAlert from "@/components/BilingualAlert";

type AlertPreview = {
  id: string;
  platform: string;
  detectedAt: string;
  verdict: "DEEPFAKE_MANIPULATION" | "EXACT_PIRACY" | "SCREEN_RECORDING";
  confidence: number;
};

// Phase-1 demo data. Replace with live /athlete/{id}/alerts endpoint once athlete auth is wired.
const DEMO_ALERTS: AlertPreview[] = [
  {
    id:         "demo-1",
    platform:   "mock-telegram",
    detectedAt: new Date().toISOString(),
    verdict:    "DEEPFAKE_MANIPULATION",
    confidence: 0.94,
  },
];

export default function AthleteView() {
  const { t } = useTranslation();
  return (
    <section className="mx-auto max-w-4xl px-6 py-10 space-y-8 bilingual">
      <header className="space-y-3">
        <h1 className="text-3xl font-bold">{t("athlete.heading")}</h1>
        <p className="text-slate-600 max-w-2xl">{t("athlete.subheading")}</p>
      </header>

      {DEMO_ALERTS.map((a) => (
        <BilingualAlert
          key={a.id}
          tone="alert"
          icon={<AlertTriangle className="h-5 w-5" aria-hidden />}
          title={t("athlete.alert.title")}
          body={
            <Trans i18nKey="athlete.alert.body" values={{ platform: a.platform }} />
          }
          meta={
            <div className="flex gap-4 text-xs text-slate-500">
              <span>Verdict: {a.verdict}</span>
              <span>Confidence: {(a.confidence * 100).toFixed(0)}%</span>
              <span>Detected: {new Date(a.detectedAt).toLocaleString()}</span>
            </div>
          }
          actions={
            <div className="flex gap-3">
              <Link
                to={`/verify/${a.id}`}
                className="rounded bg-aegis-ink text-white px-3 py-2 text-sm"
              >
                {t("athlete.seeTakedowns")}
              </Link>
            </div>
          }
        />
      ))}

      <div className="rounded-xl border border-slate-200 p-6 space-y-3">
        <div className="flex items-center gap-2 text-aegis-safe">
          <ShieldCheck className="h-5 w-5" aria-hidden />
          <h2 className="font-semibold">{t("athlete.enrol.cta")}</h2>
        </div>
        <p className="text-sm text-slate-600">
          Aegis does not build a likeness profile of an athlete who has not signed up. Enrolment is
          opt-in and can be revoked at any time. See&nbsp;
          <a className="underline" href="/docs/ethics.md">ethics policy</a>.
        </p>
        <button className="rounded bg-aegis-ink text-white px-4 py-2 text-sm">
          {t("athlete.enrol.cta")}
        </button>
      </div>
    </section>
  );
}
