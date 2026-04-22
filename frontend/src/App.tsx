import { NavLink, Route, Routes, Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Shield } from "lucide-react";
import clsx from "clsx";

import AthleteView from "@/pages/AthleteView";
import RightsHolderDashboard from "@/pages/RightsHolderDashboard";
import VerifyPage from "@/pages/VerifyPage";
import LanguageToggle from "@/components/LanguageToggle";
import ConstructedBanner from "@/components/ConstructedBanner";

// Docs live in the GitHub repo; raw markdown is not served by Firebase Hosting.
// Override at build time with VITE_AEGIS_DOCS_BASE to point at a public docs URL.
const DOCS_BASE =
  import.meta.env.VITE_AEGIS_DOCS_BASE ??
  "https://github.com/aegis-team/aegis/blob/main/docs";

export default function App() {
  const { t } = useTranslation();
  return (
    <div className="min-h-full flex flex-col">
      <ConstructedBanner />

      <header className="border-b border-slate-200">
        <div className="mx-auto max-w-6xl px-6 py-4 flex items-center gap-6">
          <NavLink to="/" className="flex items-center gap-2 font-semibold">
            <Shield className="h-5 w-5" />
            <span>{t("brand.name")}</span>
          </NavLink>
          <nav className="flex items-center gap-4 text-sm">
            <NavItem to="/">{t("nav.athlete")}</NavItem>
            <NavItem to="/rights-holder">{t("nav.rightsHolder")}</NavItem>
            <NavItem to="/verify">{t("nav.verify")}</NavItem>
          </nav>
          <div className="ml-auto">
            <LanguageToggle />
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Routes>
          {/* Athlete-facing view is the default, unauthenticated landing. */}
          <Route path="/" element={<AthleteView />} />
          <Route path="/rights-holder/*" element={<RightsHolderDashboard />} />
          <Route path="/verify" element={<VerifyPage />} />
          <Route path="/verify/:detectionId" element={<VerifyPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <footer className="border-t border-slate-200 text-xs text-slate-500">
        <div className="mx-auto max-w-6xl px-6 py-4 flex gap-4 flex-wrap">
          <span>{t("brand.tagline")}</span>
          <a className="underline" href={DOCS_BASE + "/why-not-drm.md"} target="_blank" rel="noreferrer">Why not DRM</a>
          <a className="underline" href={DOCS_BASE + "/ethics.md"} target="_blank" rel="noreferrer">Ethics</a>
          <a className="underline" href={DOCS_BASE + "/benchmarks.md"} target="_blank" rel="noreferrer">Benchmarks</a>
        </div>
      </footer>
    </div>
  );
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        clsx(
          "px-2 py-1 rounded",
          isActive ? "bg-slate-100 font-semibold" : "text-slate-600 hover:text-slate-900"
        )
      }
    >
      {children}
    </NavLink>
  );
}
