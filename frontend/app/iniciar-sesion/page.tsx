"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { mensajeError } from "@/lib/hooks";
import { guardarSesion } from "@/lib/sesion";
import type { TokenResponse } from "@/lib/types";
import { BannerError, Boton, Campo, Entrada, Tarjeta } from "@/components/ui";

export default function PaginaIniciarSesion() {
  const router = useRouter();
  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  const [errores, setErrores] = useState<string[] | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (enviando) return;
    if (correo.trim() === "" || clave === "") {
      setErrores(["Ingresa tu correo y clave"]);
      return;
    }
    setEnviando(true);
    setErrores(null);
    try {
      const respuesta = await api<TokenResponse>("/auth/login", {
        metodo: "POST",
        cuerpo: { correo: correo.trim(), clave },
      });
      guardarSesion(respuesta.token, respuesta.usuario);
      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      setErrores(error instanceof ApiError ? error.errores : [mensajeError(error)]);
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto max-w-md py-10">
      <Tarjeta>
        <h1 className="text-lg font-semibold">Iniciar sesión</h1>
        <p className="mb-5 text-sm text-slate-500">Ingresa con tu cuenta para acceder a la aplicación</p>
        <form onSubmit={enviar} className="space-y-4">
          <BannerError errores={errores} alCerrar={() => setErrores(null)} />
          <Campo etiqueta="Correo electrónico" requerido>
            <Entrada
              type="email"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              placeholder="correo@empresa.com"
              autoComplete="email"
            />
          </Campo>
          <Campo etiqueta="Clave" requerido>
            <Entrada
              type="password"
              value={clave}
              onChange={(e) => setClave(e.target.value)}
              placeholder="Tu clave"
              autoComplete="current-password"
            />
          </Campo>
          <Boton type="submit" cargando={enviando} className="w-full">
            Iniciar sesión
          </Boton>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          ¿No tienes cuenta?{" "}
          <Link href="/registrarse" className="font-medium text-sky-600 hover:underline">
            Regístrate
          </Link>
        </p>
      </Tarjeta>
    </div>
  );
}
