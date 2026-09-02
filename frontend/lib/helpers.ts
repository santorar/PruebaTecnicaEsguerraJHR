import { aCentavos } from "@/lib/decimal";
import { type Estado, type Comprobante } from "./types";
export function nombreEstado(estados: Estado[], id: number | null): string {
  return estados.find((estado) => estado.id === id)?.nombre ?? "—";
}

export function capitalizar(texto: string): string {
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

export function totales(comprobante: Comprobante) {
  const debito = comprobante.lineas.reduce((suma, linea) => suma + aCentavos(linea.debito), 0);
  const credito = comprobante.lineas.reduce((suma, linea) => suma + aCentavos(linea.credito), 0);
  return { debito, credito };
}