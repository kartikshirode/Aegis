import clsx from "clsx";
import { ReactNode } from "react";

type Props = {
  tone?: "alert" | "info" | "safe";
  icon?: ReactNode;
  title: ReactNode;
  body: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
};

const TONES: Record<NonNullable<Props["tone"]>, string> = {
  alert: "border-aegis-alert/30 bg-red-50",
  info:  "border-slate-300 bg-slate-50",
  safe:  "border-aegis-safe/30 bg-emerald-50",
};

export default function BilingualAlert({ tone = "alert", icon, title, body, meta, actions }: Props) {
  return (
    <div className={clsx("rounded-xl border p-5 space-y-3", TONES[tone])}>
      <div className="flex items-start gap-3">
        {icon && <div className="shrink-0 mt-0.5 text-aegis-alert">{icon}</div>}
        <div className="space-y-1">
          <h2 className="font-semibold">{title}</h2>
          <div className="text-sm text-slate-700">{body}</div>
        </div>
      </div>
      {meta && <div className="pl-8">{meta}</div>}
      {actions && <div className="pl-8">{actions}</div>}
    </div>
  );
}
