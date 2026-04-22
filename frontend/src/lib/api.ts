const BASE = import.meta.env.VITE_AEGIS_API_BASE ?? "http://localhost:8080";

export type VerifyResponse = {
  detection_id: string;
  verdict: string;
  confidence: number;
  merkle_receipt: null | {
    receipt_id: string;
    date: string;
    merkle_root_hex: string;
    kms_key_version: string;
    kms_signature_b64: string;
    leaf_count: number;
  };
};

export async function verifyReceipt(detectionId: string): Promise<VerifyResponse> {
  const resp = await fetch(`${BASE}/verify/${encodeURIComponent(detectionId)}`);
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`verify failed (${resp.status}) ${text}`.trim());
  }
  return resp.json();
}
