"use client";

import { useMemo, useState } from "react";
import { AccionesComprobante } from "@/components/comprobantes/acciones-comprobante";
import { Etiqueta, Seleccion, clasesTabla, cn } from "@/components/ui";
import { ESTADOS_CON_COLOR } from "@/lib/types";
import { desdeCentavos } from "@/lib/decimal";
import { fecha, moneda } from "@/lib/format";

export interface FilaComprobante {
  id: number;
  descripcion: string;
  estadoNombre: string;
  fechaCreacion: string;
  lineas: number;
  debito: number;
  credito: number;
}

type CampoOrden = keyof FilaComprobante;
type Direccion = "asc" | "desc";

const COLUMNAS: { campo: CampoOrden; texto: string; derecha?: boolean }[] = [
  { campo: "id", texto: "ID" },
  { campo: "descripcion", texto: "Descripción" },
  { campo: "estadoNombre", texto: "Estado" },
  { campo: "fechaCreacion", texto: "Fecha creación" },
  { campo: "lineas", texto: "Líneas" },
  { campo: "debito", texto: "Débitos", derecha: true },
  { campo: "credito", texto: "Créditos", derecha: true },
];

function comparar(a: FilaComprobante, b: FilaComprobante, campo: CampoOrden): number {
  const valorA = a[campo];
  const valorB = b[campo];
  if (typeof valorA === "number" && typeof valorB === "number") return valorA - valorB;
  return String(valorA).localeCompare(String(valorB), "es", { sensitivity: "base" });
}

function capitalizar(texto: string): string {
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

export function TablaComprobantes({ filas }: { filas: FilaComprobante[] }) {
  const [campo, setCampo] = useState<CampoOrden>("id");
  const [direccion, setDireccion] = useState<Direccion>("desc");
  const [pagina, setPagina] = useState(1);
  const [porPagina, setPorPagina] = useState(10);

  const ordenadas = useMemo(() => {
    const copia = [...filas];
    copia.sort((a, b) => (direccion === "asc" ? comparar(a, b, campo) : -comparar(a, b, campo)));
    return copia;
  }, [filas, campo, direccion]);

  const totalPaginas = Math.max(1, Math.ceil(ordenadas.length / porPagina));
  const paginaActual = Math.min(pagina, totalPaginas);
  const visibles = ordenadas.slice((paginaActual - 1) * porPagina, paginaActual * porPagina);

  function alternarOrden(nuevo: CampoOrden) {
    if (nuevo === campo) {
      setDireccion((actual) => (actual === "asc" ? "desc" : "asc"));
    } else {
      setCampo(nuevo);
      setDireccion("asc");
    }
    setPagina(1);
  }

  return (
    <div className="space-y-3">
      <div className={clasesTabla.contenedor}>
        <table className={clasesTabla.tabla}>
          <thead className={clasesTabla.thead}>
            <tr>
              {COLUMNAS.map((columna) => (
                <th key={columna.campo} className={cn(clasesTabla.th, columna.derecha && "text-right")}>
                  <button
                    type="button"
                    onClick={() => alternarOrden(columna.campo)}
                    className="inline-flex items-center gap-1 uppercase hover:text-sky-700"
                  >
                    {columna.texto}
                    <span
                      className={cn("text-[10px] normal-case", campo === columna.campo ? "text-sky-600" : "text-slate-300")}
                      aria-label={campo === columna.campo ? `ordenado ${direccion === "asc" ? "ascendente" : "descendente"}` : "sin ordenar"}
                    >
                      {campo === columna.campo ? (direccion === "asc" ? "▲" : "▼") : "↕"}
                    </span>
                  </button>
                </th>
              ))}
              <th className={clasesTabla.th}>Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {visibles.map((fila) => (
              <tr key={fila.id} className={clasesTabla.fila}>
                <td className={clasesTabla.td + " font-mono"}>{fila.id}</td>
                <td className={clasesTabla.td + " max-w-72 truncate"}>{fila.descripcion || "—"}</td>
                <td className={clasesTabla.td}>
                  <Etiqueta variante={ESTADOS_CON_COLOR[fila.estadoNombre] ?? "neutral"}>
                    {capitalizar(fila.estadoNombre)}
                  </Etiqueta>
                </td>
                <td className={clasesTabla.td}>{fecha(fila.fechaCreacion)}</td>
                <td className={clasesTabla.td}>{fila.lineas}</td>
                <td className={clasesTabla.td + " text-right font-mono"}>{moneda(desdeCentavos(fila.debito))}</td>
                <td className={clasesTabla.td + " text-right font-mono"}>{moneda(desdeCentavos(fila.credito))}</td>
                <td className={clasesTabla.td}>
                  <AccionesComprobante id={fila.id} nombreEstado={fila.estadoNombre} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-500">
        <div className="flex items-center gap-2">
          <label htmlFor="por-pagina" className="text-sm">
            Filas por página
          </label>
          <Seleccion
            id="por-pagina"
            value={porPagina}
            onChange={(e) => {
              setPorPagina(Number(e.target.value));
              setPagina(1);
            }}
            className="w-20"
          >
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
          </Seleccion>
          <span>· {filas.length} comprobantes</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setPagina((p) => Math.max(1, p - 1))}
            disabled={paginaActual === 1}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            ← Anterior
          </button>
          <span>
            Página {paginaActual} de {totalPaginas}
          </span>
          <button
            type="button"
            onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
            disabled={paginaActual === totalPaginas}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Siguiente →
          </button>
        </div>
      </div>
    </div>
  );
}
