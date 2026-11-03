"use client";
import MovilDemo from "@/components/MovilDemo";
import MovilReal from "@/components/MovilReal";
import { modoDemo } from "@/lib/api";

export default function CapturaMovil() {
  return modoDemo ? <MovilDemo /> : <MovilReal />;
}
