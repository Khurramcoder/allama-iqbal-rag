"use client";

import clsx from "clsx";
import { PropsWithChildren, createContext, use, useEffect, useState } from "react";

import Link from "next/link";

import type PoemType from "@/assets/content/armaghan-e-hijaz/01/01.json";

import { TranslationContext } from "./TranslationSettings";

const SizeContext = createContext<{
  setChildSize: (size: number) => void;
  maxSize: number | undefined;
  fontsLoaded: boolean;
} | null>(null);

export function Stanza({ para }: { para: (typeof PoemType)["Para"][0] }) {
  const verses = Array.isArray(para.Verse) ? para.Verse : [para.Verse];
  const { en, ur } = use(TranslationContext);

  return (
    <>
      <div className="my-4 space-y-4 text-center">
        {para.name && (
          <div dir="rtl" className="mt-8 text-2xl leading-[1.8]">
            {para.name}
          </div>
        )}
        {(para as any)["name-ur"] && (
          <div dir="rtl" className="whitespace-pre-wrap text-base leading-[2.2]">
            {(para as any)["name-ur"]}
          </div>
        )}
        {(para as any)["name-en"] && (
          <div dir="ltr" className="mx-auto max-w-screen-lg whitespace-pre-wrap text-base">
            {(para as any)["name-en"]}
          </div>
        )}
      </div>

      {verses.map((couplet) => {
        const originalText = couplet.Text.find((node) => node.lang === "Original")
          ?._content?.split("\n")
          .map((v) => v?.trim())
          .filter(Boolean);

        const urduText = couplet.Text.find((node) => node.lang === "Urdu")?._content;
        const englishText = couplet.Text.find((node) => node.lang === "English")?._content;

        const id = couplet.id;

        return (
          <SizeProvider key={id}>
            <div
              className={clsx(
                "relative w-full scroll-mt-10 border-b border-black/10 px-4 py-2 text-2xl target:bg-yellow-50",
                (en || ur) && "grid-cols-5 lg:grid lg:gap-x-10",
              )}
              id={`cplt${id}`}
            >
              <div className="relative col-span-2 flex flex-col justify-center font-mehr-nastaliq sm:ps-8">
                {id && (
                  <Link
                    href={`#cplt${id}`}
                    className="absolute inset-y-0 -start-2 hidden items-center font-sans text-xl font-black text-gray-200 transition hover:text-gray-400 sm:flex"
                  >
                    {id}
                  </Link>
                )}
                {originalText
                  ?.map((v, i) => [v, i] as const)
                  .map(([verse, index]) => (
                    <div key={index} className="flex justify-center">
                      <Verse content={verse} />
                    </div>
                  ))}
              </div>

              {(en || ur) && (
                <div className="col-span-3 mt-4 flex-col justify-center gap-y-0.5 text-center lg:mt-0 lg:flex">
                  {ur && (
                    <div className="whitespace-pre-line text-start font-mehr-nastaliq text-xl leading-[2]" dir="rtl">
                      {urduText}
                    </div>
                  )}
                  {en && (
                    <div className="whitespace-pre-line text-start font-mehr-nastaliq text-sm" dir="ltr">
                      {englishText}
                    </div>
                  )}
                </div>
              )}
            </div>
          </SizeProvider>
        );
      })}
    </>
  );
}

export function Verse({ content }: { content: string }) {
  const sizeContext = use(SizeContext);

  return (
    <div
      ref={(el) => {
        if (el?.clientWidth && sizeContext?.setChildSize && sizeContext?.fontsLoaded) {
          if ((sizeContext?.maxSize ?? 0) < el?.clientWidth) {
            sizeContext.setChildSize(el?.clientWidth + 20);
          }
        }
      }}
      key={sizeContext?.fontsLoaded ? "pending" : "loaded"}
      style={{ minWidth: sizeContext?.maxSize ? `${sizeContext?.maxSize}px` : undefined }}
      className={"inline-block w-fit whitespace-nowrap leading-[1.8] [text-align-last:justify]"}
    >
      {content}
    </div>
  );
}

export function SizeProvider({ children }: PropsWithChildren<object>) {
  const [maxSize, setMaxSize] = useState<number>();
  const [fontsLoaded, setFontsLoaded] = useState(false);

  useEffect(() => {
    document.fonts.ready.then(() => {
      setFontsLoaded(true);
    });
  }, []);

  return (
    <SizeContext.Provider
      value={{
        maxSize,
        setChildSize: (size) => {
          setMaxSize((s) => Math.max(s ?? 0, size));
        },
        fontsLoaded,
      }}
    >
      {children}
    </SizeContext.Provider>
  );
}
