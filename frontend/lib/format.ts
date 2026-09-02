const formatoMoneda = new Intl.NumberFormat("es-CO", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function moneda(valor: string | number | null | undefined): string {
  const numero = typeof valor === "number" ? valor : Number(valor ?? 0);
  return formatoMoneda.format(Number.isFinite(numero) ? numero : 0);
}

export function fecha(iso: string | null | undefined): string {
  if (!iso) return "—";
  const [parteFecha] = iso.split("T");
  const [anio, mes, dia] = parteFecha.split("-");
  if (!anio || !mes || !dia) return iso;
  return `${dia}/${mes}/${anio}`;
}

export function fechaHora(iso: string | null | undefined): string {
  if (!iso) return "—";
  const instancia = new Date(iso);
  if (Number.isNaN(instancia.getTime())) return fecha(iso);
  return instancia.toLocaleString("es-CO", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
