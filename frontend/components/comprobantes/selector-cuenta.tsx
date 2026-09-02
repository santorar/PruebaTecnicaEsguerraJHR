"use client";

import { useMemo, useRef, useState } from "react";
import type { Puc } from "@/lib/types";
import { cn, Entrada } from "@/components/ui";

interface SelectorCuentaProps {
  cuentas: Puc[];
  valor: string;
  alSeleccionar: (codigo: string) => void;
}

export function SelectorCuenta({ cuentas, valor, alSeleccionar }: SelectorCuentaProps) {
  const [busqueda, setBusqueda] = useState<string | null>(null);
  const contenedor = useRef<HTMLDivElement>(null);

  const seleccionada = cuentas.find((cuenta) => cuenta.codigo === valor) ?? null;
  const textoMostrado = busqueda ?? (seleccionada ? `${seleccionada.codigo} — ${seleccionada.nombre}` : "");

  const coincidentes = useMemo(() => {
    const consulta = (busqueda ?? "").trim().toLowerCase();
    const base = consulta
      ? cuentas.filter(
          (cuenta) =>
            cuenta.codigo.includes(consulta) || cuenta.nombre.toLowerCase().includes(consulta)
        )
      : cuentas;
    return base.slice(0, 8);
  }, [busqueda, cuentas]);

  return (
    <div
      ref={contenedor}
      className="relative"
      onBlur={(evento) => {
        if (!contenedor.current?.contains(evento.relatedTarget as Node)) setBusqueda(null);
      }}
    >
      <Entrada
        role="combobox"
        aria-expanded={busqueda !== null}
        placeholder="Buscar cuenta (código o nombre)…"
        value={textoMostrado}
        onChange={(evento) => setBusqueda(evento.target.value)}
        onFocus={() => setBusqueda("")}
        className="font-mono"
      />
      {busqueda !== null && coincidentes.length > 0 && (
        <ul className="absolute z-20 mt-1 max-h-64 w-full min-w-72 overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
          {coincidentes.map((cuenta) => (
            <li key={cuenta.codigo}>
              <button
                type="button"
                className={cn(
                  "flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-slate-100",
                  cuenta.codigo === valor && "bg-slate-50"
                )}
                onClick={() => {
                  alSeleccionar(cuenta.codigo);
                  setBusqueda(null);
                }}
              >
                <span className="font-mono text-xs text-slate-500">{cuenta.codigo}</span>
                <span className="flex-1 truncate text-slate-700">{cuenta.nombre}</span>
                <span className="text-xs font-medium text-slate-400">{cuenta.naturaleza}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
