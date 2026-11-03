"use client";
import ValidacionDemo from "@/components/ValidacionDemo";
import ValidacionReal from "@/components/ValidacionReal";
import { modoDemo } from "@/lib/api";

export default function Validacion() {
  return modoDemo ? <ValidacionDemo /> : <ValidacionReal />;
}
