import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

export function cn(...clases: Array<string | false | null | undefined>): string {
  return clases.filter(Boolean).join(" ");
}

const VARIANTES_BOTON = {
  primario: "bg-sky-900 text-white hover:bg-sky-700 border-transparent",
  secundario: "bg-white text-sky-700 hover:bg-sky-100 border-sky-300",
  peligroso: "bg-red-600 text-white hover:bg-red-500 border-transparent",
  exitoso: "bg-emerald-600 text-white hover:bg-emerald-500 border-transparent",
} as const;

interface BotonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: keyof typeof VARIANTES_BOTON;
  cargando?: boolean;
}

export function Boton({ variante = "primario", cargando = false, className, disabled, children, ...props }: BotonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        VARIANTES_BOTON[variante],
        className
      )}
      disabled={disabled || cargando}
      {...props}
    >
      {cargando && <Spinner className="h-4 w-4" />}
      {children}
    </button>
  );
}

export function Entrada({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full rounded-lg border border-sky-300 bg-white px-3 py-2 text-sm text-sky-900 placeholder:text-sky-400 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:bg-sky-100",
        className
      )}
      {...props}
    />
  );
}

export function Seleccion({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "w-full rounded-lg border border-sky-300 bg-white px-3 py-2 text-sm text-sky-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200",
        className
      )}
      {...props}
    >
      {children}
    </select>
  );
}

interface CampoProps {
  etiqueta: string;
  requerido?: boolean;
  error?: string | null;
  children: ReactNode;
}

export function Campo({ etiqueta, requerido = false, error, children }: CampoProps) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-sky-700">
        {etiqueta}
        {requerido && <span className="text-red-500"> *</span>}
      </span>
      {children}
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  );
}

const VARIANTES_ETIQUETA = {
  neutral: "bg-sky-100 text-sky-700",
  verde: "bg-emerald-100 text-emerald-700",
  rojo: "bg-red-100 text-red-700",
  amarillo: "bg-amber-100 text-amber-700",
  azul: "bg-sky-100 text-sky-700",
} as const;

export type VarianteEtiqueta = keyof typeof VARIANTES_ETIQUETA;

export function Etiqueta({ variante = "neutral", children }: { variante?: VarianteEtiqueta; children: ReactNode }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", VARIANTES_ETIQUETA[variante])}>
      {children}
    </span>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <svg className={cn("h-5 w-5 animate-spin text-sky-500", className)} viewBox="0 0 24 24" fill="none" aria-label="Cargando">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  );
}

export function Cargando({ texto = "Cargando…" }: { texto?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-12 text-sm text-sky-500">
      <Spinner />
      {texto}
    </div>
  );
}

interface BannerErrorProps {
  errores: string[] | null | undefined;
  alCerrar?: () => void;
}

export function BannerError({ errores, alCerrar }: BannerErrorProps) {
  if (!errores || errores.length === 0) return null;
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      <div className="flex items-start justify-between gap-4">
        <ul className="list-inside list-disc space-y-1">
          {errores.map((error, indice) => (
            <li key={indice}>{error}</li>
          ))}
        </ul>
        {alCerrar && (
          <button type="button" onClick={alCerrar} className="text-red-400 hover:text-red-600" aria-label="Cerrar">
            ✕
          </button>
        )}
      </div>
    </div>
  );
}

export function EstadoVacio({ titulo, descripcion }: { titulo: string; descripcion?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 py-12 text-center">
      <p className="text-sm font-medium text-sky-600">{titulo}</p>
      {descripcion && <p className="text-sm text-sky-400">{descripcion}</p>}
    </div>
  );
}

export function Tarjeta({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("rounded-xl border border-sky-200 bg-white p-6 shadow-sm", className)}>{children}</div>;
}

export const clasesTabla = {
  tabla: "min-w-full divide-y divide-sky-200 text-sm",
  thead: "bg-sky-50",
  th: "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-sky-500",
  td: "px-4 py-3 whitespace-nowrap text-sky-700",
  fila: "hover:bg-sky-50",
  contenedor: "overflow-x-auto rounded-xl border border-sky-200 bg-white shadow-sm",
};

export function Tooltip({ texto, children }: { texto: string; children: ReactNode }) {
  return (
    <span className="group relative inline-flex items-center">
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-40 mb-2 w-72 -translate-x-1/2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-normal leading-relaxed text-white opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100"
      >
        {texto}
      </span>
    </span>
  );
}
