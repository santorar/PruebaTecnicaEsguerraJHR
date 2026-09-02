import type { Usuario } from "./types";

const CLAVE_TOKEN = "balance_token";
const CLAVE_USUARIO = "balance_usuario";
export const COOKIE_TOKEN = "balance_token";
export const EVENTO_SESION = "balance:sesion";

export function guardarSesion(token: string, usuario: Usuario): void {
  localStorage.setItem(CLAVE_TOKEN, token);
  localStorage.setItem(CLAVE_USUARIO, JSON.stringify(usuario));
  document.cookie = `${COOKIE_TOKEN}=${encodeURIComponent(token)}; path=/; samesite=lax; max-age=604800`;
  window.dispatchEvent(new Event(EVENTO_SESION));
}

export function cerrarSesion(): void {
  localStorage.removeItem(CLAVE_TOKEN);
  localStorage.removeItem(CLAVE_USUARIO);
  document.cookie = `${COOKIE_TOKEN}=; path=/; samesite=lax; max-age=0`;
  window.dispatchEvent(new Event(EVENTO_SESION));
}

export function obtenerToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(CLAVE_TOKEN);
}
