"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Boton, Campo, Entrada } from "@/components/ui";

interface FiltrosLibroMayorProps {
  cuentas: string[];
  valores: { cuenta: string; fechaInicial: string; fechaFinal: string };
}

export function FiltrosLibroMayor({ cuentas, valores }: FiltrosLibroMayorProps) {
  const router = useRouter();
  const [cuenta, setCuenta] = useState(valores.cuenta);
  const [fechaInicial, setFechaInicial] = useState(valores.fechaInicial);
  const [fechaFinal, setFechaFinal] = useState(valores.fechaFinal);
  const completo = cuenta.trim() !== "" && fechaInicial !== "" && fechaFinal !== "";

  function aplicar(evento: React.FormEvent) {
    evento.preventDefault();
    if (!completo) return;
    const parametros = new URLSearchParams({ cuenta: cuenta.trim(), fecha_inicial: fechaInicial, fecha_final: fechaFinal });
    router.push(`/libro-mayor?${parametros.toString()}`);
  }

  return (
    <form onSubmit={aplicar} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="grid grid-cols-1 items-end gap-4 sm:grid-cols-4">
        <div className="sm:col-span-2">
          <Campo etiqueta="Cuenta PUC" requerido>
            <Entrada
              value={cuenta}
              onChange={(e) => setCuenta(e.target.value)}
              list="opciones-cuentas"
              placeholder="Ej. 1105"
              className="font-mono"
            />
            <datalist id="opciones-cuentas">
              {cuentas.map((codigo) => (
                <option key={codigo} value={codigo} />
              ))}
            </datalist>
          </Campo>
        </div>
        <Campo etiqueta="Fecha inicial" requerido>
          <Entrada type="date" value={fechaInicial} onChange={(e) => setFechaInicial(e.target.value)} />
        </Campo>
        <Campo etiqueta="Fecha final" requerido>
          <Entrada type="date" value={fechaFinal} onChange={(e) => setFechaFinal(e.target.value)} />
        </Campo>
      </div>
      <div className="mt-4 flex items-center gap-3">
        <Boton type="submit" disabled={!completo}>
          Consultar
        </Boton>
        {!completo && <span className="text-xs text-slate-400">Completa cuenta y rango de fechas</span>}
      </div>
    </form>
  );
}
