"use client";
import BusquedaDemo from "@/components/BusquedaDemo";
import BusquedaReal from "@/components/BusquedaReal";
import { modoDemo } from "@/lib/api";

export default function Busqueda() {
  return modoDemo ? <BusquedaDemo /> : <BusquedaReal />;
}
