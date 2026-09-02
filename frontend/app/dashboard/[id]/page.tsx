import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { apiServidor } from "@/lib/api-servidor";
import { ApiError } from "@/lib/api";
import type { Comprobante } from "@/lib/types";
import { EditorComprobante } from "@/components/comprobantes/editor-comprobante";

export const metadata: Metadata = {
  title: "Detalle de comprobante — BalanceApp",
};

async function obtenerComprobante(id: string): Promise<Comprobante> {
  let noEncontrado = false;
  let comprobante: Comprobante | null = null;
  try {
    comprobante = await apiServidor<Comprobante>(`/comprobante/${id}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      noEncontrado = true;
    } else if (error instanceof Error) {
      throw error;
    } else {
      throw new Error("No se pudo cargar el comprobante");
    }
  }
  if (noEncontrado || !comprobante) notFound();
  return comprobante;
}

export default async function PaginaComprobante({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const comprobante = await obtenerComprobante(id);
  return <EditorComprobante comprobanteInicial={comprobante} />;
}
