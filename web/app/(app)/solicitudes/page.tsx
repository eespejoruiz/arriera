import SolicitudesDemo from "@/components/SolicitudesDemo";
import SolicitudesReal from "@/components/SolicitudesReal";
import { modoDemo } from "@/lib/api";

export const metadata = { title: "Solicitudes" };

export default function Solicitudes() {
  return modoDemo ? <SolicitudesDemo /> : <SolicitudesReal />;
}
