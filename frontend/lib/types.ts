export interface Estado {
  id: number;
  nombre: string;
}

export interface Empresa {
  id: number;
  nombre: string;
  nit: string;
  dv: number | null;
  activo: boolean | null;
}

export interface Usuario {
  id: number;
  nombre: string;
  correo: string;
  empresa_id: number;
  activo: boolean | null;
}

export interface PeriodoContable {
  id: number;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  estado_id: number | null;
  estado: Estado | null;
}

export interface Puc {
  codigo: string;
  nombre: string;
  naturaleza: string;
  activo: boolean;
}

export interface TipoDocumento {
  id: number;
  nombre: string;
}

export interface Tercero {
  id: number;
  nombre: string;
  numero_documento: string;
  tipo_documento_id: number;
  activo: boolean | null;
}

export interface LineaContable {
  id?: number;
  descripcion: string | null;
  debito: string;
  credito: string;
  cuenta: string;
  tercero_id: number | null;
  comprobante_id?: number | null;
}

export interface Comprobante {
  id: number;
  descripcion: string | null;
  fecha_creacion: string | null;
  fecha_actualizacion: string | null;
  empresa_id: number;
  periodo_contable_id: number;
  usuario_id: number;
  estado_id: number | null;
  lineas: LineaContable[];
  comprobante_original_id: number | null;
  comprobante_reversor_id: number | null;
  comprobante_sustituto_id: number | null;
}

export interface LibroMayorMovimiento {
  fecha: string;
  referencia: number;
  descripcion: string;
  tercero: string | null;
  debito: string;
  credito: string;
  acumulado: string;
}

export interface ExogenaGeneracion {
  id: number;
  fecha_generacion: string;
  empresa_id: number;
  anio_gravable: number;
  umbral_uvt: string;
  valor_uvt: string;
  registros_incluidos: number;
  registros_excluidos: number;
  total_valor_bruto: string;
  total_retencion: string;
  nombre_archivo: string;
}

export interface UvtValor {
  anio: number;
  valor: string;
  fuente: string | null;
  fecha_actualizacion: string | null;
}

export interface TokenResponse {
  token: string;
  token_type: string;
  usuario: Usuario;
}

export const ESTADOS_CON_COLOR: Record<string, "amarillo" | "verde" | "rojo"> = {
  borrador: "amarillo",
  contabilizado: "verde",
  anulado: "rojo",
};
