"use client";
import CapturaDemo from "@/components/CapturaDemo";
import CapturaReal from "@/components/CapturaReal";
import { modoDemo } from "@/lib/api";

export default function Captura() {
  return modoDemo ? <CapturaDemo /> : <CapturaReal />;
}
