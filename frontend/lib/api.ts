import { obtenerToken, cerrarSesion } from "./sesion";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly errores: string[];

  constructor(status: number, errores: string[]) {
    super(errores.join(" ") || `Error ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.errores = errores;
  }
}

function mensajeDetalle(mensaje: string): string {
  return mensaje.replace(/^\d{3}:\s*/, "");
}

async function extraerErrores(response: Response): Promise<string[]> {
  let cuerpo: unknown = null;
  try {
    cuerpo = await response.json();
  } catch {
    return [`${response.status} ${response.statusText}`];
  }

  const detail = (cuerpo as { detail?: unknown })?.detail;
  if (typeof detail === "string") {
    return [mensajeDetalle(detail)];
  }
  if (Array.isArray(detail)) {
    return detail.map((error) => {
      const e = error as { loc?: unknown[]; msg?: string };
      const msg = (e.msg ?? "Error de validación").replace(/^Value error,\s*/, "");
      const campo = Array.isArray(e.loc)
        ? e.loc.filter((p) => p !== "body").join(".")
        : "";
      return campo ? `${campo}: ${msg}` : msg;
    });
  }
  return [`${response.status} ${response.statusText}`];
}

export interface OpcionesRequest {
  metodo?: "GET" | "POST" | "PUT" | "DELETE";
  cuerpo?: unknown;
  senal?: AbortSignal;
}

function construirCabeceras(cuerpo: unknown, token?: string | null): HeadersInit {
  const cabeceras: Record<string, string> = {};
  if (cuerpo !== undefined) cabeceras["Content-Type"] = "application/json";
  if (token) cabeceras["Authorization"] = `Bearer ${token}`;
  return cabeceras;
}

export async function enviarPeticion(
  ruta: string,
  opciones: OpcionesRequest,
  token?: string | null
): Promise<Response> {
  return fetch(`${API_URL}${ruta}`, {
    method: opciones.metodo ?? "GET",
    headers: construirCabeceras(opciones.cuerpo, token),
    body: opciones.cuerpo !== undefined ? JSON.stringify(opciones.cuerpo) : undefined,
    signal: opciones.senal,
    cache: "no-store",
  });
}

export async function procesarOk<T>(respuesta: Response): Promise<T> {
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await extraerErrores(respuesta));
  }
  if (respuesta.status === 204) {
    return undefined as T;
  }
  return (await respuesta.json()) as T;
}

export async function api<T>(ruta: string, opciones: OpcionesRequest = {}): Promise<T> {
  const respuesta = await enviarPeticion(ruta, opciones, obtenerToken());
  if (!respuesta.ok && respuesta.status === 401 && !ruta.startsWith("/auth/")) {
    cerrarSesion();
    window.location.reload();
  }
  return procesarOk<T>(respuesta);
}

function nombreDesdeDisposition(disposition: string | null): string | null {
  if (!disposition) return null;
  const coincidencia = /filename\*?=(?:UTF-8''|")?([^";]+)/i.exec(disposition);
  return coincidencia ? decodeURIComponent(coincidencia[1].replace(/"/g, "")) : null;
}

export interface ArchivoDescargado {
  blob: Blob;
  nombre: string;
}

export async function apiDescarga(
  ruta: string,
  opciones: OpcionesRequest = {}
): Promise<ArchivoDescargado> {
  const respuesta = await enviarPeticion(ruta, opciones, obtenerToken());
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await extraerErrores(respuesta));
  }
  const blob = await respuesta.blob();
  const nombre = nombreDesdeDisposition(respuesta.headers.get("content-disposition")) ?? "archivo.xml";
  return { blob, nombre };
}

export function descargarArchivo({ blob, nombre }: ArchivoDescargado): void {
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}
