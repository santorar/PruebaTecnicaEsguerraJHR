"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { mensajeError, useRecurso } from "@/lib/hooks";
import { useSesion } from "@/lib/sesion-react";
import { aCentavos, desdeCentavos, esValorMonetarioValido } from "@/lib/decimal";
import { moneda } from "@/lib/format";
import {
  ESTADOS_CON_COLOR,
  type Comprobante,
  type Empresa,
  type Estado,
  type PeriodoContable,
  type Puc,
  type Tercero,
} from "@/lib/types";
import {
  BannerError,
  Boton,
  Campo,
  Entrada,
  Etiqueta,
  Seleccion,
  Tarjeta,
  cn,
} from "@/components/ui";
import { SelectorCuenta } from "@/components/comprobantes/selector-cuenta";
import { ModalEmpresa } from "@/components/comprobantes/modal-empresa";
import { ModalPeriodos } from "@/components/comprobantes/modal-periodos";

function nombreEstado(estados: Estado[] | null, id: number | null | undefined): string {
  const nombre = estados?.find((estado) => estado.id === id)?.nombre;
  return nombre ? nombre.charAt(0).toUpperCase() + nombre.slice(1) : "—";
}

interface LineaEditor {
  uid: string;
  descripcion: string;
  cuenta: string;
  tercero_id: string;
  debito: string;
  credito: string;
}

interface ErroresLinea {
  cuenta?: string;
  valores?: string;
  tercero?: string;
}

let siguienteUid = 0;

function nuevoUid(base: number): string {
  return `l${base + ++siguienteUid}`;
}

function lineaVacia(uid: string): LineaEditor {
  return { uid, descripcion: "", cuenta: "", tercero_id: "", debito: "", credito: "" };
}

export function EditorComprobante({ comprobanteInicial }: { comprobanteInicial?: Comprobante }) {
  const router = useRouter();
  const baseUids = comprobanteInicial ? comprobanteInicial.lineas.length : 0;
  const inicial = comprobanteInicial ?? null;

  const { datos: estados } = useRecurso<Estado[]>("/estado/");
  const idBorrador = estados?.find((estado) => estado.nombre === "borrador")?.id ?? null;
  const idContabilizado = estados?.find((estado) => estado.nombre === "contabilizado")?.id ?? null;

  const { datos: empresas, error: errorEmpresas, recargar: recargarEmpresas } = useRecurso<Empresa[]>("/empresa/?limit=200");
  const { datos: periodos, error: errorPeriodos, recargar: recargarPeriodos } = useRecurso<PeriodoContable[]>("/periodo-contable/?limit=200");
  const { datos: cuentas, error: errorCuentas } = useRecurso<Puc[]>("/puc/?activo=true&limit=500");
  const { datos: terceros, error: errorTerceros } = useRecurso<Tercero[]>("/tercero/?limit=500");
  const sesion = useSesion();

  const [descripcion, setDescripcion] = useState(inicial?.descripcion ?? "");
  const [empresaId, setEmpresaId] = useState(inicial ? String(inicial.empresa_id) : "");
  const [periodoId, setPeriodoId] = useState(inicial ? String(inicial.periodo_contable_id) : "");
  const [usuarioId] = useState(inicial ? String(inicial.usuario_id) : "");
  const [lineas, setLineas] = useState<LineaEditor[]>(() => {
    if (inicial) {
      return inicial.lineas.map((linea, indice) => ({
        uid: `l${indice + 1}`,
        descripcion: linea.descripcion ?? "",
        cuenta: linea.cuenta,
        tercero_id: linea.tercero_id ? String(linea.tercero_id) : "",
        debito: linea.debito === "0" ? "" : linea.debito,
        credito: linea.credito === "0" ? "" : linea.credito,
      }));
    }
    return [lineaVacia(nuevoUid(0)), lineaVacia(nuevoUid(0))];
  });

  const [idActual, setIdActual] = useState<number | null>(inicial?.id ?? null);
  const [estadoActualId, setEstadoActualId] = useState<number | null>(inicial?.estado_id ?? null);
  const [errores, setErrores] = useState<string[] | null>(null);
  const [erroresPorLinea, setErroresPorLinea] = useState<Record<string, ErroresLinea>>({});
  const [mensajeExito, setMensajeExito] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const [contabilizando, setContabilizando] = useState(false);
  const [eliminando, setEliminando] = useState(false);
  const [modalEmpresaAbierto, setModalEmpresaAbierto] = useState(false);
  const [modalPeriodosAbierto, setModalPeriodosAbierto] = useState(false);

  const esBorrador = idBorrador !== null && estadoActualId === idBorrador;
  const esContabilizado = idContabilizado !== null && estadoActualId === idContabilizado;
  const editable = !inicial || esBorrador || esContabilizado;

  const empresaEfectiva = empresaId || (empresas && empresas.length > 0 ? String(empresas[0].id) : "");
  const periodoEfectivo = useMemo(() => {
    if (periodoId || !periodos || periodos.length === 0) return periodoId;
    const abierto = periodos.find((periodo) => periodo.estado?.nombre === "abierto");
    return String((abierto ?? periodos[0]).id);
  }, [periodoId, periodos]);
  const usuarioEfectivo = usuarioId || (sesion ? String(sesion.id) : "");

  const totalDebito = useMemo(() => lineas.reduce((suma, linea) => suma + aCentavos(linea.debito), 0), [lineas]);
  const totalCredito = useMemo(() => lineas.reduce((suma, linea) => suma + aCentavos(linea.credito), 0), [lineas]);
  const diferencia = totalDebito - totalCredito;
  const balanceado = diferencia === 0;

  function actualizarLinea(uid: string, cambios: Partial<LineaEditor>) {
    setLineas((anteriores) => anteriores.map((linea) => (linea.uid === uid ? { ...linea, ...cambios } : linea)));
    setErroresPorLinea((anteriores) => {
      if (!anteriores[uid]) return anteriores;
      const restantes = { ...anteriores };
      delete restantes[uid];
      return restantes;
    });
  }

  function agregarLinea() {
    setLineas((anteriores) => [...anteriores, lineaVacia(nuevoUid(baseUids))]);
  }

  function eliminarLinea(uid: string) {
    setLineas((anteriores) => anteriores.filter((linea) => linea.uid !== uid));
  }

  function cambiarValor(uid: string, campo: "debito" | "credito", valor: string) {
    if (!esValorMonetarioValido(valor)) return;
    const cambios: Partial<LineaEditor> = { [campo]: valor };
    if (campo === "debito" && valor !== "") cambios.credito = "";
    if (campo === "credito" && valor !== "") cambios.debito = "";
    actualizarLinea(uid, cambios);
  }

  function validar(): string[] {
    const globales: string[] = [];
    const porLinea: Record<string, ErroresLinea> = {};

    if (!empresaEfectiva) globales.push("Selecciona la empresa");
    if (!periodoEfectivo) globales.push("Selecciona el periodo contable");
    if (!usuarioEfectivo) globales.push("Inicia sesión para registrar comprobantes");

    if (lineas.length < 2) {
      globales.push("El comprobante debe tener al menos dos líneas contables");
    }

    for (const linea of lineas) {
      const erroresLinea: ErroresLinea = {};
      if (!linea.cuenta) {
        erroresLinea.cuenta = "El código de la cuenta no puede estar vacío";
      } else if (cuentas && !cuentas.some((cuenta) => cuenta.codigo === linea.cuenta)) {
        erroresLinea.cuenta = `La cuenta '${linea.cuenta}' no existe en el PUC`;
      }
      const debito = aCentavos(linea.debito);
      const credito = aCentavos(linea.credito);
      if (debito < 0 || credito < 0) {
        erroresLinea.valores = "Los valores de débito y crédito no pueden ser negativos";
      } else if (debito > 0 && credito > 0) {
        erroresLinea.valores = "Una línea contable no puede tener valores de débito y crédito al mismo tiempo";
      }
      if (erroresLinea.cuenta || erroresLinea.valores) porLinea[linea.uid] = erroresLinea;
    }

    setErroresPorLinea(porLinea);
    if (lineas.length >= 2 && !balanceado) {
      globales.push("El total de débito debe ser igual al total de crédito");
    }
    return globales;
  }

  function construirCuerpo() {
    return {
      descripcion: descripcion.trim() || null,
      empresa_id: Number(empresaEfectiva),
      periodo_contable_id: Number(periodoEfectivo),
      usuario_id: Number(usuarioEfectivo),
      lineas: lineas.map((linea) => ({
        descripcion: linea.descripcion.trim() || null,
        cuenta: linea.cuenta,
        tercero_id: linea.tercero_id ? Number(linea.tercero_id) : null,
        debito: linea.debito === "" ? "0" : linea.debito,
        credito: linea.credito === "" ? "0" : linea.credito,
      })),
    };
  }

  async function guardar(): Promise<Comprobante> {
    if (idActual) {
      const actualizado = await api<Comprobante>(`/comprobante/${idActual}`, {
        metodo: "PUT",
        cuerpo: construirCuerpo(),
      });
      return actualizado;
    }
    const creado = await api<Comprobante>("/comprobante/", {
      metodo: "POST",
      cuerpo: construirCuerpo(),
    });
    return creado;
  }

  async function manejarGuardarBorrador() {
    setMensajeExito(null);
    const globales = validar();
    if (globales.length > 0) {
      setErrores(globales);
      return;
    }
    setGuardando(true);
    setErrores(null);
    try {
      const guardado = await guardar();
      setIdActual(guardado.id);
      setEstadoActualId(guardado.estado_id ?? null);
      if (inicial && guardado.id !== inicial.id) {
        setMensajeExito(
          `Se creó el comprobante #${guardado.id} (borrador) que reemplaza al #${inicial.id}, que quedó anulado.`
        );
      } else {
        setMensajeExito("Borrador guardado correctamente. Ya puedes contabilizarlo o seguir editándolo.");
      }
      router.refresh();
    } catch (error) {
      setErrores(error instanceof ApiError ? error.errores : [mensajeError(error)]);
    } finally {
      setGuardando(false);
    }
  }

  async function manejarContabilizar() {
    setMensajeExito(null);
    const globales = validar();
    if (globales.length > 0) {
      setErrores(globales);
      return;
    }
    if (idContabilizado === null) {
      setErrores(["No se pudo resolver el estado 'contabilizado'. Verifica que exista en el catálogo de estados."]);
      return;
    }
    setContabilizando(true);
    setErrores(null);
    try {
      const guardado = await guardar();
      setIdActual(guardado.id);
      setEstadoActualId(guardado.estado_id ?? null);
      await api<Comprobante>(`/comprobante/${guardado.id}/estado/${idContabilizado}`, { metodo: "PUT" });
      router.push("/dashboard");
    } catch (error) {
      setErrores(error instanceof ApiError ? error.errores : [mensajeError(error)]);
      setContabilizando(false);
    }
  }

  async function manejarEliminar() {
    if (!idActual || !window.confirm("¿Eliminar este borrador? Esta acción no se puede deshacer.")) return;
    setEliminando(true);
    setErrores(null);
    try {
      await api(`/comprobante/${idActual}`, { metodo: "DELETE" });
      router.push("/dashboard");
    } catch (error) {
      setErrores(error instanceof ApiError ? error.errores : [mensajeError(error)]);
      setEliminando(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-sm text-slate-500 hover:text-slate-800">
            ← Volver
          </Link>
          <h1 className="text-xl font-semibold">
            {inicial ? `Comprobante #${inicial.id}` : "Nuevo comprobante"}
          </h1>
          {estadoActualId !== null && (
            <Etiqueta variante={ESTADOS_CON_COLOR[nombreEstado(estados, estadoActualId).toLowerCase()] ?? "neutral"}>
              {nombreEstado(estados, estadoActualId)}
            </Etiqueta>
          )}
        </div>
        <div className="flex items-center gap-2">
          {mensajeExito && <span className="text-sm text-emerald-600">{mensajeExito}</span>}
          {editable && (
            <>
              {esBorrador && idActual && (
                <Boton variante="peligroso" onClick={manejarEliminar} cargando={eliminando} disabled={guardando || contabilizando}>
                  Eliminar
                </Boton>
              )}
              <Boton variante="secundario" onClick={manejarGuardarBorrador} cargando={guardando} disabled={contabilizando}>
                {esContabilizado ? "Guardar cambios" : "Guardar borrador"}
              </Boton>
              {(esBorrador || !inicial) && (
                <Boton variante="exitoso" onClick={manejarContabilizar} cargando={contabilizando} disabled={guardando || idContabilizado === null}>
                  Contabilizar
                </Boton>
              )}
            </>
          )}
        </div>
      </div>

      {inicial && esContabilizado && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          Este comprobante ya está <strong>contabilizado</strong>. Al guardarlo, el sistema creará automáticamente un{" "}
          <strong>comprobante reversor</strong> que anula este documento y un{" "}
          <strong>nuevo comprobante en borrador</strong> con los cambios que registres.
        </div>
      )}

      <BannerError errores={errores} alCerrar={() => setErrores(null)} />
      <BannerError
        errores={[errorEmpresas, errorPeriodos, errorCuentas, errorTerceros].filter(
          (error): error is string => Boolean(error)
        )}
      />

      <Tarjeta>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-700">
                Empresa <span className="text-red-500">*</span>
              </span>
              {editable && (
                <button
                  type="button"
                  onClick={() => setModalEmpresaAbierto(true)}
                  className="text-xs font-medium text-sky-600 hover:underline"
                >
                  + Nueva
                </button>
              )}
            </div>
            <Seleccion value={empresaEfectiva} onChange={(e) => setEmpresaId(e.target.value)} disabled={!editable}>
              <option value="">{empresas ? "Selecciona una empresa" : "Cargando…"}</option>
              {empresas?.map((empresa) => (
                <option key={empresa.id} value={empresa.id}>
                  {empresa.nombre} (NIT {empresa.nit})
                </option>
              ))}
            </Seleccion>
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-700">
                Periodo contable <span className="text-red-500">*</span>
              </span>
              {editable && (
                <button
                  type="button"
                  onClick={() => setModalPeriodosAbierto(true)}
                  className="text-xs font-medium text-sky-600 hover:underline"
                >
                  + Gestionar
                </button>
              )}
            </div>
            <Seleccion value={periodoEfectivo} onChange={(e) => setPeriodoId(e.target.value)} disabled={!editable}>
              <option value="">{periodos ? "Selecciona un periodo" : "Cargando…"}</option>
              {periodos?.map((periodo) => (
                <option key={periodo.id} value={periodo.id}>
                  {periodo.nombre} — {periodo.estado?.nombre ?? "sin estado"}
                </option>
              ))}
            </Seleccion>
          </div>
          <Campo etiqueta="Usuario" requerido>
            <div className="rounded-lg border border-sky-200 bg-sky-50/50 px-3 py-2 text-sm text-slate-600">
              {sesion ? sesion.nombre : "Sin sesión activa"}
            </div>
          </Campo>
          <div className="sm:col-span-3">
            <Campo etiqueta="Descripción">
              <Entrada
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                placeholder="Descripción del comprobante…"
                disabled={!editable}
              />
            </Campo>
          </div>
        </div>
      </Tarjeta>

      <Tarjeta className="p-0" >
        <div className="overflow-x-auto rounded-xl">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="w-10 px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">#</th>
                <th className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Cuenta</th>
                <th className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Tercero</th>
                <th className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Descripción</th>
                <th className="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Débito</th>
                <th className="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Crédito</th>
                <th className="w-10 px-3 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {lineas.map((linea, indice) => {
                const erroresLinea = erroresPorLinea[linea.uid];
                return (
                  <tr key={linea.uid} className="align-top">
                    <td className="px-3 py-3 text-slate-400">{indice + 1}</td>
                    <td className="px-3 py-3">
                      <div className="min-w-64">
                        {editable ? (
                          <SelectorCuenta
                            cuentas={cuentas ?? []}
                            valor={linea.cuenta}
                            alSeleccionar={(codigo) => actualizarLinea(linea.uid, { cuenta: codigo })}
                          />
                        ) : (
                          <span className="font-mono text-xs">{linea.cuenta}</span>
                        )}
                        {erroresLinea?.cuenta && <p className="mt-1 text-xs text-red-600">{erroresLinea.cuenta}</p>}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <Seleccion
                        value={linea.tercero_id}
                        onChange={(e) => actualizarLinea(linea.uid, { tercero_id: e.target.value })}
                        disabled={!editable}
                        className="min-w-44"
                      >
                        <option value="">Sin tercero</option>
                        {terceros?.map((tercero) => (
                          <option key={tercero.id} value={tercero.id}>
                            {tercero.nombre} — {tercero.numero_documento}
                          </option>
                        ))}
                      </Seleccion>
                    </td>
                    <td className="px-3 py-3">
                      <Entrada
                        value={linea.descripcion}
                        onChange={(e) => actualizarLinea(linea.uid, { descripcion: e.target.value })}
                        placeholder="Descripción…"
                        disabled={!editable}
                        className="min-w-40"
                      />
                    </td>
                    <td className="px-3 py-3">
                      <Entrada
                        value={linea.debito}
                        onChange={(e) => cambiarValor(linea.uid, "debito", e.target.value)}
                        placeholder="0"
                        inputMode="decimal"
                        disabled={!editable}
                        className="w-32 text-right font-mono"
                      />
                    </td>
                    <td className="px-3 py-3">
                      <Entrada
                        value={linea.credito}
                        onChange={(e) => cambiarValor(linea.uid, "credito", e.target.value)}
                        placeholder="0"
                        inputMode="decimal"
                        disabled={!editable}
                        className="w-32 text-right font-mono"
                      />
                    </td>
                    <td className="px-3 py-3">
                      {editable && (
                        <button
                          type="button"
                          onClick={() => eliminarLinea(linea.uid)}
                          className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
                          aria-label={`Eliminar línea ${indice + 1}`}
                        >
                          ✕
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot className="bg-slate-50 font-medium">
              <tr>
                <td colSpan={4} className="px-3 py-3 text-right text-slate-600">
                  Totales
                </td>
                <td className="px-3 py-3 text-right font-mono text-slate-900">{moneda(desdeCentavos(totalDebito))}</td>
                <td className="px-3 py-3 text-right font-mono text-slate-900">{moneda(desdeCentavos(totalCredito))}</td>
                <td />
              </tr>
              <tr>
                <td colSpan={4} className="px-3 py-3 text-right text-slate-600">
                  Diferencia
                </td>
                <td colSpan={2} className={cn("px-3 py-3 text-right font-mono", balanceado ? "text-emerald-600" : "text-red-600")}>
                  {moneda(desdeCentavos(Math.abs(diferencia)))} {balanceado ? "✓ cuadrado" : "(descuadre)"}
                </td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
        {editable && (
          <div className="border-t border-slate-100 p-4">
            <Boton variante="secundario" onClick={agregarLinea}>
              + Agregar línea
            </Boton>
          </div>
        )}
      </Tarjeta>

      <ModalEmpresa
        abierto={modalEmpresaAbierto}
        alCerrar={() => setModalEmpresaAbierto(false)}
        alCrear={(empresa) => {
          setEmpresaId(String(empresa.id));
          recargarEmpresas();
        }}
      />
      <ModalPeriodos
        abierto={modalPeriodosAbierto}
        alCerrar={() => setModalPeriodosAbierto(false)}
        periodos={periodos}
        estados={estados}
        alCrear={(periodo) => {
          setPeriodoId(String(periodo.id));
          recargarPeriodos();
        }}
        alActualizar={recargarPeriodos}
      />
    </div>
  );
}
