"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { mensajeError, useRecurso } from "@/lib/hooks";
import { guardarSesion } from "@/lib/sesion";
import type { Empresa, TokenResponse, Usuario } from "@/lib/types";
import { BannerError, Boton, Campo, Entrada, Seleccion, Tarjeta } from "@/components/ui";

export default function PaginaRegistrarse() {
  const router = useRouter();
  const { datos: empresas } = useRecurso<Empresa[]>("/empresa/?limit=200");
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [empresaId, setEmpresaId] = useState("");
  const [errores, setErrores] = useState<string[] | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (enviando) return;
    const erroresLocales: string[] = [];
    if (nombre.trim() === "") erroresLocales.push("El nombre es obligatorio");
    if (correo.trim() === "") erroresLocales.push("El correo es obligatorio");
    if (clave.length < 6) erroresLocales.push("La clave debe tener al menos 6 caracteres");
    if (clave !== confirmacion) erroresLocales.push("Las claves no coinciden");
    if (empresaId === "") erroresLocales.push("Selecciona la empresa a la que perteneces");
    if (erroresLocales.length > 0) {
      setErrores(erroresLocales);
      return;
    }
    setEnviando(true);
    setErrores(null);
    try {
      await api<Usuario>("/auth/registro", {
        metodo: "POST",
        cuerpo: {
          nombre: nombre.trim(),
          correo: correo.trim(),
          clave,
          confirmacion_clave: confirmacion,
          empresa_id: Number(empresaId),
        },
      });
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
        <h1 className="text-lg font-semibold">Registrarse</h1>
        <p className="mb-5 text-sm text-slate-500">Crea tu cuenta de usuario</p>
        <form onSubmit={enviar} className="space-y-4">
          <BannerError errores={errores} alCerrar={() => setErrores(null)} />
          <Campo etiqueta="Nombre" requerido>
            <Entrada value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Tu nombre" />
          </Campo>
          <Campo etiqueta="Correo electrónico" requerido>
            <Entrada
              type="email"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              placeholder="correo@empresa.com"
              autoComplete="email"
            />
          </Campo>
          <Campo etiqueta="Empresa" requerido>
            <Seleccion value={empresaId} onChange={(e) => setEmpresaId(e.target.value)}>
              <option value="">{empresas ? "Selecciona una empresa" : "Cargando…"}</option>
              {empresas?.map((empresa) => (
                <option key={empresa.id} value={empresa.id}>
                  {empresa.nombre} (NIT {empresa.nit})
                </option>
              ))}
            </Seleccion>
          </Campo>
          <Campo etiqueta="Clave" requerido>
            <Entrada
              type="password"
              value={clave}
              onChange={(e) => setClave(e.target.value)}
              placeholder="Mínimo 6 caracteres"
              autoComplete="new-password"
            />
          </Campo>
          <Campo etiqueta="Confirmar clave" requerido>
            <Entrada
              type="password"
              value={confirmacion}
              onChange={(e) => setConfirmacion(e.target.value)}
              placeholder="Repite la clave"
              autoComplete="new-password"
            />
          </Campo>
          <Boton type="submit" cargando={enviando} className="w-full">
            Crear cuenta
          </Boton>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          ¿Ya tienes cuenta?{" "}
          <Link href="/iniciar-sesion" className="font-medium text-sky-600 hover:underline">
            Inicia sesión
          </Link>
        </p>
      </Tarjeta>
    </div>
  );
}
