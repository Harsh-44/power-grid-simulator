import { useId } from "react";
import type { ReactNode, Ref } from "react";

export default function Drawer({
  panelRef,
  title,
  description,
  presentation = "drawer",
  children,
}: {
  panelRef: Ref<HTMLDialogElement>;
  title: string;
  description?: string;
  presentation?: "drawer" | "modal";
  children: ReactNode;
}) {
  const titleId = useId();
  const descriptionId = `${titleId}-description`;
  return (
    <dialog
      ref={panelRef}
      aria-labelledby={titleId}
      aria-describedby={description ? descriptionId : undefined}
      className={`fixed overflow-hidden bg-white p-0 text-slate-900 shadow-xl backdrop:bg-slate-900/30 ${
        presentation === "modal"
          ? "inset-0 m-auto h-[min(44rem,calc(100dvh-2rem))] max-h-none w-[calc(100%-2rem)] max-w-3xl rounded-xl border border-slate-200"
          : "inset-y-0 right-auto left-0 m-0 h-dvh max-h-none w-full max-w-full sm:w-[30rem]"
      }`}
    >
      <div className="flex h-full min-h-0 flex-col">
        <header className="flex items-center justify-between gap-4 border-b border-slate-200 px-4 py-3 sm:px-6">
          <div className="min-w-0">
            <h2 id={titleId} className="text-base font-semibold tracking-tight">{title}</h2>
            {description && <p id={descriptionId} className="mt-0.5 text-[13px] text-slate-600">{description}</p>}
          </div>
          <form method="dialog">
            <button
              type="submit"
              aria-label={`Close ${title.toLowerCase()}`}
              className="grid size-8 place-items-center rounded-md border border-slate-200 text-xl leading-none text-slate-600 transition-colors hover:bg-slate-100"
            >
              <span aria-hidden="true">×</span>
            </button>
          </form>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain bg-[#f6f8fb] p-4 sm:p-6">{children}</div>
      </div>
    </dialog>
  );
}
