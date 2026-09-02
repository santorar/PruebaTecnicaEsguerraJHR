import { apiServidor } from "@/lib/api-servidor";
import { fechaHora, moneda } from "@/lib/format";
import type { Empresa, ExogenaGeneracion } from "@/lib/types";
import { EstadoVacio, clasesTabla } from "@/components/ui";
import { FormGeneracion } from "@/components/exogena/form-generacion";
import { BotonRedescarga } from "@/components/exogena/boton-redescarga";

function nombreEmpresa(empresas: Empresa[], id: number): string {
  return empresas.find((empresa) => empresa.id === id)?.nombre ?? `Empresa ${id}`;
}

export default async function PaginaExogena() {
  const [empresas, historial] = await Promise.all([
    apiServidor<Empresa[]>("/empresa/?limit=200"),
    apiServidor<ExogenaGeneracion[]>("/api/exogena/historial?limit=100"),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Información exógena</h1>
        <p className="text-sm text-sky-500">
          Generación del reporte XML a partir de los movimientos contables con terceros
        </p>
      </div>

      <FormGeneracion empresas={empresas} />

      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-sky-700">Historial de generaciones</h2>
        {historial.length === 0 ? (
          <div className="rounded-xl border border-sky-200 bg-white shadow-sm">
            <EstadoVacio
              titulo="Aún no se han generado reportes"
              descripcion="Configura los parámetros y genera el primer XML de información exógena."
            />
          </div>
        ) : (
          <div className={clasesTabla.contenedor}>
            <table className={clasesTabla.tabla}>
              <thead className={clasesTabla.thead}>
                <tr>
                  <th className={clasesTabla.th}>ID</th>
                  <th className={clasesTabla.th}>Fecha generación</th>
                  <th className={clasesTabla.th}>Empresa</th>
                  <th className={clasesTabla.th}>Año gravable</th>
                  <th className={clasesTabla.th + " text-right"}>Umbral (UVT)</th>
                  <th className={clasesTabla.th + " text-right"}>Valor UVT</th>
                  <th className={clasesTabla.th + " text-right"}>Registros</th>
                  <th className={clasesTabla.th + " text-right"}>Total bruto</th>
                  <th className={clasesTabla.th + " text-right"}>Total retención</th>
                  <th className={clasesTabla.th}>Archivo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-sky-100">
                {historial.map((generacion) => (
                  <tr key={generacion.id} className={clasesTabla.fila}>
                    <td className={clasesTabla.td + " font-mono"}>{generacion.id}</td>
                    <td className={clasesTabla.td}>{fechaHora(generacion.fecha_generacion)}</td>
                    <td className={clasesTabla.td + " max-w-48 truncate"}>
                      {nombreEmpresa(empresas, generacion.empresa_id)}
                    </td>
                    <td className={clasesTabla.td + " font-mono"}>{generacion.anio_gravable}</td>
                    <td className={clasesTabla.td + " text-right font-mono"}>{moneda(generacion.umbral_uvt)}</td>
                    <td className={clasesTabla.td + " text-right font-mono"}>{moneda(generacion.valor_uvt)}</td>
                    <td className={clasesTabla.td + " text-right font-mono"}>
                      {generacion.registros_incluidos}
                      {generacion.registros_excluidos > 0 && (
                        <span className="text-xs text-sky-400"> (+{generacion.registros_excluidos} excl.)</span>
                      )}
                    </td>
                    <td className={clasesTabla.td + " text-right font-mono"}>{moneda(generacion.total_valor_bruto)}</td>
                    <td className={clasesTabla.td + " text-right font-mono"}>{moneda(generacion.total_retencion)}</td>
                    <td className={clasesTabla.td}>
                      <BotonRedescarga idGeneracion={generacion.id} />
                      <span className="mt-1 block max-w-40 truncate font-mono text-xs text-sky-400">
                        {generacion.nombre_archivo}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
