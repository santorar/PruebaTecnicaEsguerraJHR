"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";

interface EstadoRecurso<T> {
  datos: T | null;
  cargando: boolean;
  error: string | null;
  recargar: () => void;
}

interface EstadoInterno<T> {
  ruta: string | null;
  intento: number;
  datos: T | null;
  error: string | null;
}

export function useRecurso<T>(ruta: string | null): EstadoRecurso<T> {
  const [intento, setIntento] = useState(0);
  const [estado, setEstado] = useState<EstadoInterno<T>>({
    ruta,
    intento: 0,
    datos: null,
    error: null,
  });

  useEffect(() => {
    if (!ruta) return;
    const control = new AbortController();
    api<T>(ruta, { senal: control.signal })
      .then((respuesta) =>
        setEstado({ ruta, intento, datos: respuesta, error: null })
      )
      .catch((error: unknown) => {
        if (esAborto(error)) return;
        setEstado({
          ruta,
          intento,
          datos: null,
          error:
            error instanceof ApiError
              ? error.errores.join(" ")
              : "No se pudo conectar con el servidor",
        });
      });
    return () => control.abort();
  }, [ruta, intento]);

  const recargar = useCallback(() => setIntento((i) => i + 1), []);

  const pendiente = estado.ruta !== ruta || estado.intento !== intento;
  return {
    datos: pendiente ? null : estado.datos,
    cargando: ruta !== null && pendiente,
    error: pendiente ? null : estado.error,
    recargar,
  };
}

export function esAborto(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

export function mensajeError(error: unknown): string {
  if (error instanceof ApiError) return error.errores.join(" ");
  if (error instanceof Error) return error.message;
  return "Ocurrió un error inesperado";
}
