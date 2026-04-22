import { useTranslation } from "react-i18next";

// Per docs/case-study.md, every demo surface must carry this disclosure so
// judges can never mistake the fictional "Test-Subject Meera" persona for a
// real person. Keep it permanent, not dismissible.
export default function ConstructedBanner() {
  const { t } = useTranslation();
  return (
    <div className="bg-aegis-ink text-white text-xs">
      <div className="mx-auto max-w-6xl px-6 py-1.5 text-center bilingual">
        {t("constructed.banner")}
      </div>
    </div>
  );
}
