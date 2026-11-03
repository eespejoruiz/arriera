import AuditoriaDemo from "@/components/AuditoriaDemo";
import CumplimientoReal from "@/components/CumplimientoReal";
import { modoDemo } from "@/lib/api";

export const metadata = { title: "Auditoría" };

export default function Auditoria() {
  return modoDemo ? <AuditoriaDemo /> : <CumplimientoReal />;
}
