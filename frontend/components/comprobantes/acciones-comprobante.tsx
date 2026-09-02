"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Boton, Tooltip } from "@/components/ui";
import { Modal } from "@/components/modal";

const TEXTO_TOOLTIP =
  "Al editar un comprobante contabilizado, el sistema crea automáticamente un comprobante reversor que anula el documento errado y un nuevo comprobante en borrador con los cambios que registres.";

export function AccionesComprobante({ id, nombreEstado }: { id: number; nombreEstado: string }) {
  const router = useRouter();
  const [advertencia, setAdvertencia] = useState(false);

  if (nombreEstado === "borrador") {
    return (
      <Link href={`/dashboard/${id}`} className="text-sm font-medium text-slate-700 underline-offset-2 hover:underline">
        Editar
      </Link>
    );
  }

  if (nombreEstado === "contabilizado") {
    return (
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setAdvertencia(true)}
          className="text-sm font-medium text-slate-700 underline-offset-2 hover:underline"
        >
          Editar
        </button>
        <Tooltip texto={TEXTO_TOOLTIP}>
          <span
            tabIndex={0}
            aria-label="Más información sobre editar un comprobante contabilizado"
            className="flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-slate-400 text-[10px] font-semibold text-slate-500"
          >
            i
          </span>
        </Tooltip>
        <Modal abierto={advertencia} alCerrar={() => setAdvertencia(false)} titulo="Este comprobante ya está contabilizado">
          <div className="space-y-3 text-sm text-slate-600">
            <p>Si lo editas, el sistema hará lo siguiente de forma automática:</p>
            <ul className="list-inside list-disc space-y-1">
              <li>
                Creará un <strong>comprobante reversor</strong> que anula el documento errado.
              </li>
              <li>
                Creará un <strong>nuevo comprobante en borrador</strong> con los cambios que registres.
              </li>
            </ul>
            <p>¿Estás seguro de que deseas editarlo?</p>
          </div>
          <div className="mt-6 flex justify-end gap-2">
            <Boton variante="secundario" onClick={() => setAdvertencia(false)}>
              Cancelar
            </Boton>
            <Boton variante="primario" onClick={() => router.push(`/dashboard/${id}`)}>
              Sí, editar
            </Boton>
          </div>
        </Modal>
      </div>
    );
  }

  return (
    <Link href={`/dashboard/${id}`} className="text-sm font-medium text-slate-700 underline-offset-2 hover:underline">
      Ver
    </Link>
  );
}
