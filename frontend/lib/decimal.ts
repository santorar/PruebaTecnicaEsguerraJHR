export function aCentavos(valor: string | number | null | undefined): number {
  if (valor === null || valor === undefined || valor === "") return 0;
  const numero = typeof valor === "number" ? valor : Number(valor);
  if (!Number.isFinite(numero)) return 0;
  return Math.round(numero * 100);
}

export function desdeCentavos(centavos: number): string {
  return (centavos / 100).toFixed(2);
}

export function tieneMasDeDosDecimales(valor: string): boolean {
  const indice = valor.indexOf(".");
  if (indice === -1) return false;
  return valor.length - indice - 1 > 2;
}

export function esValorMonetarioValido(valor: string): boolean {
  if (valor === "") return true;
  return /^\d*\.?\d*$/.test(valor) && !tieneMasDeDosDecimales(valor);
}
