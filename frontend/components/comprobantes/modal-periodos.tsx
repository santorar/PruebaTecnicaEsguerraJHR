"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { mensajeError } from "@/lib/hooks";
import { fecha } from "@/lib/format";
import type { Estado, PeriodoContable } from "@/lib/types";
import { BannerError, Boton, Campo, Entrada, Etiqueta, Tooltip } from "@/components/ui";
import { Modal } from "@/components/modal";

interface ModalPeriodosProps {
  abierto: boolean;
  alCerrar: () => void;
  periodos: PeriodoContable[] | null;
  estados: Estado[] | null;
  alCrear: (periodo: PeriodoContable) => void;
  alActualizar: () => void;
}

export function ModalPeriodos({ abierto, alCerrar, periodos, estados, alCrear, alActualizar }: ModalPeriodosProps) {
  const [nombre, setNombre] = useState("");
  const [fechaInicial, setFechaInicial] = useState("");
  const [fechaFinal, setFechaFinal] = useState("");
  const [errores, setErrores] = useState<string[] | null>(null);
  const [creando, setCreando] = useState(false);
  const [cerrandoId, setCerrandoId] = useState<number | null>(null);

  const idCerrado = estados?.find((estado) => estado.nombre === "cerrado")?.id ?? null;

  function nombreEstado(id: number | null): string {
    const nombre = estados?.find((estado) => estado.id === id)?.nombre ?? "—";
    return nombre.charAt(0).toUpperCase() + nombre.slice(1);
  }

  async function crear(evento: React.FormEvent) {
    evento.preventDefault();
    if (creando) return;
    const erroresLocales: string[] = [];
    if (nombre.trim() === "") erroresLocales.push("El nombre del periodo es obligatorio");
    if (fechaInicial === "" || fechaFinal === "") {
      erroresLocales.push("Las fechas de inicio y fin son obligatorias");
    } else if (fechaFinal < fechaInicial) {
      erroresLocales.push("La fecha final no puede ser anterior a la inicial");
    }
    if (erroresLocales.length > 0) {
      setErrores(erroresLocales);
      return;
    }
    setCreando(true);
    setErrores(null);
    try {
      const periodo = await api<PeriodoContable>("/periodo-contable/", {
        metodo: "POST",
        cuerpo: { nombre: nombre.trim(), fecha_inicio: fechaInicial, fecha_fin: fechaFinal },
      });
      alCrear(periodo);
      setNombre("");
      setFechaInicial("");
      setFechaFinal("");
    } catch (error) {
      setErrores(error instanceof ApiError ? error.errores : [mensajeError(error)]);
    } finally {
      setCreando(false);
    }
  }

  async function cerrar(periodo: PeriodoContable) {
    if (idCerrado === null) {
      setErrores(["No se pudo resolver el estado 'cerrado'. Verifica que exista en el catálogo de estados."]);
      return;
    }
    if (!window.confirm(`¿Cerrar el periodo ${periodo.nombre}? No se podrán contabilizar más comprobantes en él.`)) return;
    setCerrandoId(periodo.id);
    setErrores(null);
    try {
      await api<PeriodoContable>(`/periodo-contable/${periodo.id}/estado/${idCerrado}`, { metodo: "PUT" });
      alActualizar();
    } catch (error) {
      setErrores(error instanceof ApiError ? error.errores : [mensajeError(error)]);
    } finally {
      setCerrandoId(null);
    }
  }

  return (
    <Modal abierto={abierto} alCerrar={alCerrar} titulo="Periodos contables">
      <div className="space-y-6">
        <form onSubmit={crear} className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-700">Nuevo periodo</h3>
          <BannerError errores={errores} alCerrar={() => setErrores(null)} />
          <Campo etiqueta="Nombre" requerido>
            <Entrada
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej. 2026-09"
            />
          </Campo>
          <div className="grid grid-cols-2 gap-4">
            <Campo etiqueta="Fecha inicial" requerido>
              <Entrada type="date" value={fechaInicial} onChange={(e) => setFechaInicial(e.target.value)} />
            </Campo>
            <Campo etiqueta="Fecha final" requerido>
              <Entrada type="date" value={fechaFinal} onChange={(e) => setFechaFinal(e.target.value)} />
            </Campo>
          </div>
          <div className="flex justify-end">
            <Boton type="submit" cargando={creando}>
              Crear periodo
            </Boton>
          </div>
        </form>

        <div>
          <h3 className="mb-2 text-sm font-semibold text-slate-700">Periodos existentes</h3>
          {!periodos || periodos.length === 0 ? (
            <p className="text-sm text-slate-400">No hay periodos registrados.</p>
          ) : (
            <ul className="divide-y divide-sky-100 rounded-lg border border-sky-100">
              {periodos.map((periodo) => {
                const nombre = nombreEstado(periodo.estado_id);
                const abierto = nombre.toLowerCase() === "abierto";
                return (
                  <li key={periodo.id} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                    <div>
                      <p className="font-medium text-slate-700">{periodo.nombre}</p>
                      <p className="text-xs text-slate-400">
                        {fecha(periodo.fecha_inicio)} — {fecha(periodo.fecha_fin)}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <Etiqueta variante={abierto ? "verde" : "neutral"}>{nombre}</Etiqueta>
                      {abierto && (
                        <Tooltip texto="Al cerrar el periodo no se podrán contabilizar más comprobantes en él.">
                          <button
                            type="button"
                            onClick={() => cerrar(periodo)}
                            disabled={cerrandoId !== null}
                            className="text-xs font-medium text-red-600 hover:underline disabled:opacity-50"
                          >
                            {cerrandoId === periodo.id ? "Cerrando…" : "Cerrar"}
                          </button>
                        </Tooltip>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="flex justify-end">
          <Boton variante="secundario" onClick={alCerrar}>
            Listo
          </Boton>
        </div>
      </div>
    </Modal>
  );
}
