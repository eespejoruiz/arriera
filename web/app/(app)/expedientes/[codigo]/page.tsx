import Visor from "./Visor";
export const metadata = { title: "Expediente 2018-0412" };
export function generateStaticParams() { return [{ codigo: "2018-0412" }]; }
export default function Expediente() { return <Visor />; }
