import { Suspense } from "react";
import { ApiError } from "@/lib/api";
import { apiServidor } from "@/lib/api-servidor";
import { aCentavos, desdeCentavos } from "@/lib/decimal";
import { fecha, moneda } from "@/lib/format";
import type { LibroMayorMovimiento, Puc } from "@/lib/types";
import { BannerError, Cargando, EstadoVacio, Tarjeta, clasesTabla } from "@/components/ui";
import { FiltrosLibroMayor } from "@/components/libro-mayor/filtros";

interface Props {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

function texto(searchParams: Record<string, string | string[] | undefined>, clave: string): string {
  const valor = searchParams[clave];
  return typeof valor === "string" ? valor : "";
}

async function ResultadosLibroMayor({
  cuenta,
  fechaInicial,
  fechaFinal,
}: {
  cuenta: string;
  fechaInicial: string;
  fechaFinal: string;
}) {
  let movimientos: LibroMayorMovimiento[];
  let error: string | null = null;
  try {
    movimientos = await apiServidor<LibroMayorMovimiento[]>("/libro_mayor/", {
      metodo: "POST",
      cuerpo: { cuenta, fecha_inicial: fechaInicial, fecha_final: fechaFinal },
    });
  } catch (excepcion) {
    if (!(excepcion instanceof ApiError)) throw excepcion;
    error = excepcion.errores.join(" ");
    return (
      <Tarjeta>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Movimientos</h2>
        <BannerError errores={[error]} />
      </Tarjeta>
    );
  }

  if (movimientos.length === 0) {
    return (
      <Tarjeta>
        <EstadoVacio
          titulo="Sin movimientos"
          descripcion={`La cuenta ${cuenta} no tiene movimientos entre ${fecha(fechaInicial)} y ${fecha(fechaFinal)}.`}
        />
      </Tarjeta>
    );
  }

  const totalDebito = movimientos.reduce((suma, m) => suma + aCentavos(m.debito), 0);
  const totalCredito = movimientos.reduce((suma, m) => suma + aCentavos(m.credito), 0);
  const saldoFinal = movimientos[movimientos.length - 1].acumulado;

  return (
    <div className={clasesTabla.contenedor}>
      <table className={clasesTabla.tabla}>
        <thead className={clasesTabla.thead}>
          <tr>
            <th className={clasesTabla.th}>Fecha</th>
            <th className={clasesTabla.th}>Comprobante</th>
            <th className={clasesTabla.th}>Descripción</th>
            <th className={clasesTabla.th}>Tercero</th>
            <th className={clasesTabla.th + " text-right"}>Débito</th>
            <th className={clasesTabla.th + " text-right"}>Crédito</th>
            <th className={clasesTabla.th + " text-right"}>Saldo</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {movimientos.map((movimiento, indice) => (
            <tr key={indice} className={clasesTabla.fila}>
              <td className={clasesTabla.td}>{fecha(movimiento.fecha)}</td>
              <td className={clasesTabla.td + " font-mono"}>#{movimiento.referencia}</td>
              <td className={clasesTabla.td + " max-w-64 truncate"}>{movimiento.descripcion || "—"}</td>
              <td className={clasesTabla.td}>{movimiento.tercero ?? "—"}</td>
              <td className={clasesTabla.td + " text-right font-mono"}>{moneda(movimiento.debito)}</td>
              <td className={clasesTabla.td + " text-right font-mono"}>{moneda(movimiento.credito)}</td>
              <td className={clasesTabla.td + " text-right font-mono font-medium"}>{moneda(movimiento.acumulado)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot className="bg-slate-50 font-medium">
          <tr>
            <td colSpan={4} className="px-4 py-3 text-right text-slate-600">
              Totales
            </td>
            <td className="px-4 py-3 text-right font-mono">{moneda(desdeCentavos(totalDebito))}</td>
            <td className="px-4 py-3 text-right font-mono">{moneda(desdeCentavos(totalCredito))}</td>
            <td className="px-4 py-3 text-right font-mono">{moneda(saldoFinal)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

export default async function PaginaLibroMayor({ searchParams }: Props) {
  const parametros = await searchParams;
  const cuenta = texto(parametros, "cuenta");
  const fechaInicial = texto(parametros, "fecha_inicial");
  const fechaFinal = texto(parametros, "fecha_final");
  const filtrosActivos = cuenta !== "" && fechaInicial !== "" && fechaFinal !== "";
  const cuentas = await apiServidor<Puc[]>("/puc/?activo=true&limit=500");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Libro mayor</h1>
        <p className="text-sm text-slate-500">
          Movimientos contables por cuenta con saldo acumulado
        </p>
      </div>

      <FiltrosLibroMayor
        cuentas={cuentas.map((c) => c.codigo)}
        valores={{ cuenta, fechaInicial, fechaFinal }}
      />

      {filtrosActivos ? (
        <Suspense
          key={`${cuenta}|${fechaInicial}|${fechaFinal}`}
          fallback={
            <Tarjeta>
              <Cargando texto="Consultando movimientos…" />
            </Tarjeta>
          }
        >
          <ResultadosLibroMayor cuenta={cuenta} fechaInicial={fechaInicial} fechaFinal={fechaFinal} />
        </Suspense>
      ) : (
        <Tarjeta>
          <EstadoVacio
            titulo="Aplica los filtros para consultar"
            descripcion="Selecciona una cuenta y un rango de fechas, luego presiona «Consultar»."
          />
        </Tarjeta>
      )}
    </div>
  );
}
