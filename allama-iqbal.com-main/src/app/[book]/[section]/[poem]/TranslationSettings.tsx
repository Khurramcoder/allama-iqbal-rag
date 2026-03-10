"use client";

import { ReactNode, createContext, use, useCallback } from "react";

import { Cog8ToothIcon } from "@heroicons/react/24/outline";
import { useLocalStorage } from "@mantine/hooks";
import * as Popover from "@radix-ui/react-popover";

interface TranslationContextProps {
  ur: boolean;
  en: boolean;
  toggleTranslation: (lang: "en" | "ur", val: boolean) => void;
}

export const TranslationContext = createContext<TranslationContextProps>({
  ur: true,
  en: true,
  toggleTranslation: () => undefined,
});

export function TranslationSettingsProvider({ children }: { children: ReactNode }) {
  const [ur, setUr] = useLocalStorage({
    key: "ur-translation",
    defaultValue: true,
  });
  const [en, setEn] = useLocalStorage({
    key: "en-translation",
    defaultValue: true,
  });

  const toggleTranslation = useCallback(
    (lang: "en" | "ur", val: boolean) => {
      if (lang === "ur") {
        setUr(val);
      }
      if (lang === "en") {
        setEn(val);
      }
    },
    [setEn, setUr],
  );

  return <TranslationContext.Provider value={{ ur, en, toggleTranslation }}>{children}</TranslationContext.Provider>;
}

export function TranslationSettings() {
  const { en, ur, toggleTranslation } = use(TranslationContext);

  return (
    <Popover.Root>
      <Popover.Trigger className="-m-2.5 p-2.5 text-gray-400 hover:text-gray-500">
        <span className="sr-only">Translation Settings</span>
        <Cog8ToothIcon strokeWidth={1.5} className="size-6" />
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          sideOffset={4}
          align="end"
          className="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 w-48 rounded border border-gray-200 bg-white p-4 shadow-md outline-none"
        >
          <p className="mb-2.5 font-medium">Translation Settings</p>

          <div className="space-y-2">
            <label className="flex cursor-pointer items-center gap-x-2.5">
              <input
                className="rounded-sm"
                checked={en}
                onChange={(e) => toggleTranslation("en", e.target.checked)}
                type="checkbox"
              />
              <div>English</div>
            </label>
            <label className="flex cursor-pointer items-center gap-x-2.5">
              <input
                className="rounded-sm"
                checked={ur}
                onChange={(e) => toggleTranslation("ur", e.target.checked)}
                type="checkbox"
              />
              <div>Urdu</div>
            </label>
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
