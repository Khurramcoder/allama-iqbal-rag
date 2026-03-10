"use client";

import { useEffect } from "react";

import { usePathname, useSearchParams } from "next/navigation";

export default function PatchLocationHash() {
  const params = useSearchParams();
  const pathName = usePathname();

  useEffect(() => {
    const hash = params.get("hash");

    if (hash) {
      window.location = `#${hash}` as any;
    }
  }, [params, pathName]);

  return null;
}
