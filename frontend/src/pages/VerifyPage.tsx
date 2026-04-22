import { useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { verifyReceipt, type VerifyResponse } from "@/lib/api";

export default function VerifyPage() {
  const { t } = useTranslation();
  const params = useParams<{ detectionId?: string }>();
  const [detectionId, setDetectionId] = useState(params.detectionId ?? "");
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      const r = await verifyReceipt(detectionId.trim());
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="mx-auto max-w-2xl px-6 py-10 space-y-6 bilingual">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold">{t("verify.heading")}</h1>
        <p className="text-slate-600">{t("verify.subheading")}</p>
      </header>

      <form className="space-y-3" onSubmit={onSubmit}>
        <label className="block text-sm font-medium" htmlFor="det">
          {t("verify.input")}
        </label>
        <input
          id="det"
          value={detectionId}
          onChange={(e) => setDetectionId(e.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2 font-mono text-sm"
          placeholder="e.g. 3f1c…"
          required
        />
        <button
          type="submit"
          disabled={pending || !detectionId.trim()}
          className="rounded bg-aegis-ink text-white px-4 py-2 text-sm disabled:opacity-50"
        >
          {pending ? "…" : t("verify.button")}
        </button>
      </form>

      {error && <div className="rounded bg-red-50 text-red-800 text-sm p-3">{error}</div>}

      {result && (
        <div className="rounded-xl border border-slate-200 p-5 space-y-3">
          <div className="text-sm">Verdict: <span className="font-mono">{result.verdict}</span></div>
          <div className="text-sm">Confidence: {(result.confidence * 100).toFixed(0)}%</div>
          {result.merkle_receipt ? (
            <dl className="grid grid-cols-[8rem_1fr] gap-y-1 text-xs">
              <dt className="text-slate-500">Receipt date</dt>
              <dd className="font-mono">{result.merkle_receipt.date}</dd>
              <dt className="text-slate-500">Merkle root</dt>
              <dd className="font-mono break-all">{result.merkle_receipt.merkle_root_hex}</dd>
              <dt className="text-slate-500">KMS key version</dt>
              <dd className="font-mono">{result.merkle_receipt.kms_key_version}</dd>
              <dt className="text-slate-500">Leaves</dt>
              <dd>{result.merkle_receipt.leaf_count}</dd>
            </dl>
          ) : (
            <div className="text-xs text-slate-500">
              No Merkle anchor yet — anchors are computed at end of day.
            </div>
          )}
        </div>
      )}
    </section>
  );
}
