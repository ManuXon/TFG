// useWindowWidthHook.ts
import { useState, useEffect } from "react";

export function useWindowWidth() {
  const [w, setW] = useState<number>(() =>
    typeof window !== "undefined" ? window.innerWidth : 1024
  );

  useEffect(() => {
    const onResize = () => setW(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return w;
}
