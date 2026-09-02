import Link from "next/link";
import Image from "next/image";
import Ilustration404 from "@/public/404.svg";

export default function NoEncontrado() {
  return (
    <div className="py-16 text-center">
      <Image src={Ilustration404} alt="Ilustración de error 404" className="mx-auto h-100 w-auto" />
      <h1 className="text-xl font-semibold">Página no encontrada</h1>
      <p className="mt-2 text-sm text-slate-500">El recurso que buscas no existe o fue eliminado.</p>
      <Link href="/dashboard" className="mt-4 inline-block text-sm font-medium text-slate-700 underline underline-offset-2">
        Volver al dashboard
      </Link>
    </div>
  );
}
