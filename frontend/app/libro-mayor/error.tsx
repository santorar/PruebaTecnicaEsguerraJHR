"use client";

import { BannerError, Boton } from "@/components/ui";

export default function ErrorLibroMayor({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="space-y-4 py-8">
      <h1 className="text-lg font-semibold">No se pudo cargar el libro mayor</h1>
      <BannerError errores={[error.message]} />
      <Boton variante="secundario" onClick={reset}>
        Reintentar
      </Boton>
    </div>
  );
}
