"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { mensajeError } from "@/lib/hooks";
import type { Empresa } from "@/lib/types";
import { BannerError, Boton, Campo, Entrada } from "@/components/ui";
import { Modal } from "@/components/modal";

interface ModalEmpresaProps {
  abierto: boolean;
  alCerrar: () => void;
  alCrear: (empresa: Empresa) => void;
}

export function ModalEmpresa({ abierto, alCerrar, alCrear }: ModalEmpresaProps) {
  const [nombre, setNombre] = useState("");
  const [nit, setNit] = useState("");
  const [errores, setErrores] = useState<string[] | null>(null);
  const [creando, setCreando] = useState(false);

  async function crear(evento: React.FormEvent) {
    evento.preventDefault();
    if (creando) return;
    const erroresLocales: string[] = [];
    if (nombre.trim() === "") erroresLocales.push("El nombre es obligatorio");
    if (!/^\d{2,}$/.test(nit.trim())) {
      erroresLocales.push("El NIT debe contener al menos 2 dígitos numéricos");
    }
    if (erroresLocales.length > 0) {
      setErrores(erroresLocales);
      return;
    }
    setCreando(true);
    setErrores(null);
    try {
      const empresa = await api<Empresa>("/empresa/", {
        metodo: "POST",
        cuerpo: { nombre: nombre.trim(), nit: nit.trim() },
      });
      alCrear(empresa);
      setNombre("");
      setNit("");
      alCerrar();
    } catch (error) {
      setErrores(error instanceof ApiError ? error.errores : [mensajeError(error)]);
    } finally {
      setCreando(false);
    }
  }

  return (
    <Modal abierto={abierto} alCerrar={alCerrar} titulo="Nueva empresa">
      <form onSubmit={crear} className="space-y-4">
        <BannerError errores={errores} alCerrar={() => setErrores(null)} />
        <Campo etiqueta="Nombre" requerido>
          <Entrada
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Nombre de la empresa…"
          />
        </Campo>
        <Campo etiqueta="NIT" requerido>
          <Entrada
            value={nit}
            onChange={(e) => /^\d*$/.test(e.target.value) && setNit(e.target.value)}
            inputMode="numeric"
            placeholder="Solo dígitos; el dígito de verificación se calcula automáticamente"
          />
        </Campo>
        <div className="flex justify-end gap-2 pt-2">
          <Boton type="button" variante="secundario" onClick={alCerrar}>
            Cancelar
          </Boton>
          <Boton type="submit" cargando={creando}>
            Crear empresa
          </Boton>
        </div>
      </form>
    </Modal>
  );
}
