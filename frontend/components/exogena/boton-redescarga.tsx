"use client";

import { useState } from "react";
import { apiDescarga, ApiError, descargarArchivo } from "@/lib/api";
import { mensajeError } from "@/lib/hooks";

export function BotonRedescarga({ idGeneracion }: { idGeneracion: number }) {
  const [descargando, setDescargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function redescargar() {
    setDescargando(true);
    setError(null);
    try {
      const archivo = await apiDescarga(`/api/exogena/historial/${idGeneracion}/archivo`);
      descargarArchivo(archivo);
    } catch (excepcion) {
      setError(excepcion instanceof ApiError ? excepcion.errores.join(" ") : mensajeError(excepcion));
    } finally {
      setDescargando(false);
    }
  }

  return (
    <div className="flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={redescargar}
        disabled={descargando}
        className="text-sm font-medium text-slate-700 underline underline-offset-2 hover:text-slate-900 disabled:opacity-50"
      >
        {descargando ? "Descargando…" : "Re-descargar"}
      </button>
      {error && <span className="max-w-56 text-xs text-red-600">{error}</span>}
    </div>
  );
}
