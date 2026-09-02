import Link from "next/link";
import { apiServidor } from "@/lib/api-servidor";
import { aCentavos } from "@/lib/decimal";
import type { Comprobante, Estado } from "@/lib/types";
import { Boton, EstadoVacio } from "@/components/ui";
import { TablaComprobantes, type FilaComprobante } from "@/components/comprobantes/tabla-comprobantes";

function nombreEstado(estados: Estado[], id: number | null): string {
  return estados.find((estado) => estado.id === id)?.nombre ?? "—";
}

function totales(comprobante: Comprobante) {
  const debito = comprobante.lineas.reduce((suma, linea) => suma + aCentavos(linea.debito), 0);
  const credito = comprobante.lineas.reduce((suma, linea) => suma + aCentavos(linea.credito), 0);
  return { debito, credito };
}

export default async function PaginaComprobantes() {
  const [comprobantes, estados] = await Promise.all([
    apiServidor<Comprobante[]>("/comprobante/?limit=500"),
    apiServidor<Estado[]>("/estado/"),
  ]);

  const filas: FilaComprobante[] = comprobantes.map((comprobante) => {
    const { debito, credito } = totales(comprobante);
    return {
      id: comprobante.id,
      descripcion: comprobante.descripcion ?? "",
      estadoNombre: nombreEstado(estados, comprobante.estado_id),
      fechaCreacion: comprobante.fecha_creacion ?? "",
      lineas: comprobante.lineas.length,
      debito,
      credito,
    };
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Comprobantes</h1>
          <p className="text-sm text-slate-500">Registro y gestión de comprobantes contables</p>
        </div>
        <Link href="/dashboard/nuevo">
          <Boton>+ Nuevo comprobante</Boton>
        </Link>
      </div>

      {filas.length === 0 ? (
        <div className="rounded-xl border border-sky-200 bg-white shadow-sm">
          <EstadoVacio
            titulo="No hay comprobantes registrados"
            descripcion="Crea tu primer comprobante con el botón «Nuevo comprobante»."
          />
        </div>
      ) : (
        <TablaComprobantes filas={filas} />
      )}
    </div>
  );
}
