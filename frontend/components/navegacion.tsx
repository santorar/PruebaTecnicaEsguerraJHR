"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cerrarSesion } from "@/lib/sesion";
import { useSesion } from "@/lib/sesion-react";

const ENLACES = [
  { href: "/dashboard", texto: "Comprobantes" },
  { href: "/libro-mayor", texto: "Libro mayor" },
  { href: "/exogena", texto: "Información exógena" },
];

export function Navegacion() {
  const ruta = usePathname();
  const router = useRouter();
  const sesion = useSesion();
  const enVistaSesion = ruta === "/iniciar-sesion" || ruta === "/registrarse";

  return (
    <header className="border-b border-sky-100 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4">
        <Link href="/" className="text-2xl font-semibold text-sky-900">
          BalanceApp
        </Link>
        {!enVistaSesion && (
          <>
            <nav className="flex items-center gap-1">
              {ENLACES.map((enlace) => {
                const activo = ruta === enlace.href || ruta.startsWith(`${enlace.href}/`);
                return (
                  <Link
                    key={enlace.href}
                    href={enlace.href}
                    className={
                      activo
                        ? "rounded-lg bg-sky-900 px-3 py-1.5 text-sm font-medium text-white"
                        : "rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-sky-50"
                    }
                  >
                    {enlace.texto}
                  </Link>
                );
              })}
            </nav>
            {sesion ? (
              <div className="flex items-center gap-3">
                <span className="text-sm text-slate-600">{sesion.nombre}</span>
                <button
                  type="button"
                  onClick={() => {
                    cerrarSesion();
                    router.push("/iniciar-sesion");
                    router.refresh();
                  }}
                  className="rounded-lg border border-sky-200 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-sky-50"
                >
                  Cerrar sesión
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/iniciar-sesion"
                  className="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-sky-50"
                >
                  Iniciar sesión
                </Link>
                <Link
                  href="/registrarse"
                  className="rounded-lg bg-sky-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-800"
                >
                  Registrarse
                </Link>
              </div>
            )}
          </>
        )}
      </div>
    </header>
  );
}
