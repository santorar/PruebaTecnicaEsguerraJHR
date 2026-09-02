"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiDescarga, ApiError, descargarArchivo } from "@/lib/api";
import { mensajeError, useRecurso } from "@/lib/hooks";
import { aCentavos, desdeCentavos, esValorMonetarioValido } from "@/lib/decimal";
import { moneda } from "@/lib/format";
import type { Empresa, UvtValor } from "@/lib/types";
import { BannerError, Boton, Campo, Entrada, Seleccion } from "@/components/ui";

interface FormGeneracionProps {
  empresas: Empresa[];
}

export function FormGeneracion({ empresas }: FormGeneracionProps) {
  const router = useRouter();
  const anioActual = new Date().getFullYear();
  const { datos: uvt } = useRecurso<UvtValor[]>("/api/exogena/uvt");

  const [empresaId, setEmpresaId] = useState(empresas.length > 0 ? String(empresas[0].id) : "");
  const [anioGravable, setAnioGravable] = useState(String(anioActual));
  const [umbral, setUmbral] = useState("");
  const [errores, setErrores] = useState<string[] | null>(null);
  const [mensajeExito, setMensajeExito] = useState<string | null>(null);
  const [generando, setGenerando] = useState(false);

  const uvtDelAnio = useMemo(
    () => uvt?.find((registro) => registro.anio === Number(anioGravable)) ?? null,
    [uvt, anioGravable]
  );
  const umbralEnPesos = uvtDelAnio
    ? aCentavos(uvtDelAnio.valor) * aCentavos(umbral === "" ? "0" : umbral) / 100
    : 0;

  async function generar(evento: React.FormEvent) {
    evento.preventDefault();
    setMensajeExito(null);

    const erroresLocales: string[] = [];
    if (!empresaId) erroresLocales.push("Selecciona la empresa");
    const anio = Number(anioGravable);
    if (!Number.isInteger(anio) || anio < 1900 || anio > 2199) {
      erroresLocales.push("El año gravable debe estar entre 1900 y 2199");
    }
    if (!esValorMonetarioValido(umbral) || aCentavos(umbral) < 0) {
      erroresLocales.push("El umbral en UVT no puede ser negativo");
    }
    if (erroresLocales.length > 0) {
      setErrores(erroresLocales);
      return;
    }

    setGenerando(true);
    setErrores(null);
    try {
      const archivo = await apiDescarga("/api/exogena/generar", {
        metodo: "POST",
        cuerpo: {
          empresa_id: Number(empresaId),
          anio_gravable: anio,
          umbral_uvt: umbral === "" ? "0" : umbral,
        },
      });
      descargarArchivo(archivo);
      setMensajeExito(`XML generado: ${archivo.nombre}`);
      router.refresh();
    } catch (error) {
      setErrores(error instanceof ApiError ? error.errores : [mensajeError(error)]);
    } finally {
      setGenerando(false);
    }
  }

  return (
    <form onSubmit={generar} className="rounded-xl border border-sky-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-sm font-semibold text-sky-700">Parámetros de generación</h2>
      <BannerError errores={errores} alCerrar={() => setErrores(null)} />
      {mensajeExito && (
        <p className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {mensajeExito}
        </p>
      )}
      <div className="grid grid-cols-1 items-end gap-4 sm:grid-cols-3">
        <Campo etiqueta="Empresa" requerido>
          <Seleccion value={empresaId} onChange={(e) => setEmpresaId(e.target.value)}>
            <option value="">{empresas.length > 0 ? "Selecciona una empresa" : "No hay empresas"}</option>
            {empresas.map((empresa) => (
              <option key={empresa.id} value={empresa.id}>
                {empresa.nombre} (NIT {empresa.nit}-{empresa.dv})
              </option>
            ))}
          </Seleccion>
        </Campo>
        <Campo etiqueta="Año gravable" requerido>
          <Entrada
            value={anioGravable}
            onChange={(e) => setAnioGravable(e.target.value.replace(/\D/g, ""))}
            inputMode="numeric"
            placeholder={String(anioActual)}
          />
        </Campo>
        <Campo etiqueta="Umbral (UVT)" error={uvtDelAnio ? undefined : "Sin valor de UVT para este año"}>
          <Entrada
            value={umbral}
            onChange={(e) => esValorMonetarioValido(e.target.value) && setUmbral(e.target.value)}
            inputMode="decimal"
            placeholder="0 = sin filtro"
          />
        </Campo>
      </div>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-sky-500">
          {uvtDelAnio ? (
            <>
              UVT {uvtDelAnio.anio}: <span className="font-mono">{moneda(uvtDelAnio.valor)}</span>
              {umbral !== "" && (
                <>
                  {" "}· umbral equivalente a{" "}
                  <span className="font-mono">{moneda(desdeCentavos(umbralEnPesos))}</span> COP
                </>
              )}
            </>
          ) : (
            "El valor de la UVT se consulta automáticamente (fuente externa con fallback local)."
          )}
        </p>
        <Boton type="submit" cargando={generando} disabled={empresas.length === 0}>
          Generar y descargar XML
        </Boton>
      </div>
    </form>
  );
}
