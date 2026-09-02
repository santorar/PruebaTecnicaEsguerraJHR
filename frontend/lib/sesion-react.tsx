"use client";

import { useSyncExternalStore } from "react";
import { EVENTO_SESION } from "./sesion";
import type { Usuario } from "./types";

const CLAVE_TOKEN = "balance_token";
const CLAVE_USUARIO = "balance_usuario";

function leerSesionCruda(): string {
  return `${localStorage.getItem(CLAVE_TOKEN) ?? ""}|${localStorage.getItem(CLAVE_USUARIO) ?? ""}`;
}

function suscribirseSesion(cambio: () => void): () => void {
  window.addEventListener("storage", cambio);
  window.addEventListener(EVENTO_SESION, cambio);
  return () => {
    window.removeEventListener("storage", cambio);
    window.removeEventListener(EVENTO_SESION, cambio);
  };
}

export function useSesion(): Usuario | null {
  const crudo = useSyncExternalStore(suscribirseSesion, leerSesionCruda, () => "");
  const partes = crudo.split("|");
  const token = partes[0] ?? "";
  const usuarioCrudo = partes[1] ?? "";
  if (!token || !usuarioCrudo) return null;
  try {
    return JSON.parse(usuarioCrudo) as Usuario;
  } catch {
    return null;
  }
}
