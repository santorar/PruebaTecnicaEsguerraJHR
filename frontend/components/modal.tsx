"use client";

import { useEffect, type ReactNode } from "react";

interface ModalProps {
  abierto: boolean;
  alCerrar: () => void;
  titulo: string;
  children: ReactNode;
}

export function Modal({ abierto, alCerrar, titulo, children }: ModalProps) {
  useEffect(() => {
    if (!abierto) return;
    const manejarTecla = (evento: KeyboardEvent) => {
      if (evento.key === "Escape") alCerrar();
    };
    window.addEventListener("keydown", manejarTecla);
    return () => window.removeEventListener("keydown", manejarTecla);
  }, [abierto, alCerrar]);

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label={titulo}>
      <div className="absolute inset-0 bg-slate-900/50" onClick={alCerrar} />
      <div className="relative w-full max-w-lg rounded-xl border border-sky-200 bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="text-base font-semibold text-slate-900">{titulo}</h2>
          <button type="button" onClick={alCerrar} className="text-slate-400 hover:text-slate-600" aria-label="Cerrar">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
