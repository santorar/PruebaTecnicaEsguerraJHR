import type { Metadata } from "next";
import { EditorComprobante } from "@/components/comprobantes/editor-comprobante";

export const metadata: Metadata = {
  title: "Nuevo comprobante — BalanceApp",
};

export default function PaginaNuevoComprobante() {
  return <EditorComprobante />;
}
