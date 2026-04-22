import { useTranslation } from "react-i18next";
import clsx from "clsx";

const LANGS = [
  { code: "en", label: "EN" },
  { code: "hi", label: "हिं" },
] as const;

export default function LanguageToggle() {
  const { i18n } = useTranslation();
  return (
    <div className="inline-flex rounded border border-slate-200 overflow-hidden text-xs">
      {LANGS.map((l) => (
        <button
          key={l.code}
          onClick={() => i18n.changeLanguage(l.code)}
          className={clsx(
            "px-2 py-1",
            i18n.language.startsWith(l.code)
              ? "bg-aegis-ink text-white"
              : "bg-white text-slate-600 hover:bg-slate-50",
          )}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
