import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { COOKIE_TOKEN } from "./sesion";
import { enviarPeticion, procesarOk, type OpcionesRequest } from "./api";

export async function apiServidor<T>(ruta: string, opciones: OpcionesRequest = {}): Promise<T> {
  const almacen = await cookies();
  const token = almacen.get(COOKIE_TOKEN)?.value;
  const respuesta = await enviarPeticion(ruta, opciones, token);
  if (respuesta.status === 401) {
    redirect("/iniciar-sesion");
  }
  return procesarOk<T>(respuesta);
}
