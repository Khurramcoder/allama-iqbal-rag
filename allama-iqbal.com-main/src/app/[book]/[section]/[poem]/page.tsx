import { Suspense } from "react";

import { ChevronLeftIcon, ChevronRightIcon } from "@heroicons/react/20/solid";
import { Metadata } from "next";
import Link from "next/link";

import type PoemType from "@/assets/content/armaghan-e-hijaz/01/01.json";
import PatchLocationHash from "@/components/PatchLocationHash";
import { findAdjacentPoems } from "@/utils/books";

import { TranslationSettings, TranslationSettingsProvider } from "./TranslationSettings";
import { SizeProvider, Stanza } from "./components";

type Props = {
  params: Promise<{ book: string; section: string; poem: string }>;
};

export default async function Poem({ params }: Props) {
  const { book, section, poem: poemId } = await params;

  const poem = await import(`../../../../assets/content/${book}/${section}/${poemId}.json`).then(
    (m) => m.default as typeof PoemType,
  );

  const { next, prev } = findAdjacentPoems(book, section, poemId);

  return (
    <TranslationSettingsProvider>
      <Suspense fallback={null}>
        <PatchLocationHash />
      </Suspense>
      <div className="px-4 py-10 text-center font-nastaliq leading-[2] sm:px-6 md:px-4 lg:px-12" dir="rtl">
        <div dir="ltr" className="flex max-w-fit items-center gap-x-4">
          <TranslationSettings />
        </div>

        <div
          dir="rtl"
          className="mx-auto mb-10 w-full max-w-6xl whitespace-pre-wrap text-center font-nastaliq leading-[2]"
        >
          <Link href={poem.sectionId ? `/${poem.bookId}#${poem.sectionId}` : `/${poem.bookId}`} dir="rtl">
            {poem.bookName} {poem.sectionName && <>&#183; {poem.sectionName}</>}
          </Link>
          {poem.name && <div className="mt-4 text-4xl leading-[2]">{poem.name}</div>}
          {(poem as any)["name-ur"] && (
            <div dir="rtl" className="leading-[2.2]">
              {(poem as any)["name-ur"]}
            </div>
          )}
          {poem["name-en"] && <div dir="ltr">{poem["name-en"]}</div>}
        </div>

        <div className="mx-auto flex w-full max-w-6xl flex-col items-center justify-center font-nastaliq leading-[2.2] @container">
          {poem.Para.map((para) => (
            <SizeProvider key={para.id}>
              <Stanza para={para} />
            </SizeProvider>
          ))}
        </div>

        {(poem as { credits?: string }).credits && (
          <div dir="ltr" className="mx-auto my-2 w-full max-w-6xl px-4 py-2 text-start text-sm text-gray-600">
            {(poem as { credits?: string }).credits}
          </div>
        )}

        <div className="mx-auto mt-24 flex w-full max-w-6xl justify-between gap-x-10 px-4 pb-10 font-nastaliq leading-[1.8] sm:grid-cols-2">
          {next && (
            <Link
              href={`/${next.book.slug}/${next.section.slug}/${next.slug}`}
              className="flex items-center justify-start gap-x-4 pe-10 text-start text-xl font-semibold"
            >
              <ChevronRightIcon className="relative -bottom-4 size-8" />
              <div className="space-y-4 text-lg">
                <div className="text-xs">{[next.book.name, next.section.name].filter(Boolean).join(" > ")}</div>
                <div>{next.name}</div>
              </div>
            </Link>
          )}
          {prev ? (
            <Link
              href={`/${prev.book.slug}/${prev.section.slug}/${prev.slug}`}
              className="hidden items-center justify-end gap-x-4 ps-10 text-end text-xl md:flex"
            >
              <div className="space-y-4 text-lg">
                <div className="text-xs">{[prev.book.name, prev.section.name].filter(Boolean).join(" > ")}</div>
                <div>{prev.name}</div>
              </div>
              <ChevronLeftIcon className="relative -bottom-4 size-8" />
            </Link>
          ) : (
            <span />
          )}
        </div>
      </div>
    </TranslationSettingsProvider>
  );
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { book, section, poem: poemId } = await params;

  const poem = await import(`../../../../assets/content/${book}/${section}/${poemId}.json`).then(
    (m) => m.default as typeof PoemType,
  );

  const description = `Explore the profound words of Allama Iqbal in '${poem?.name}' from his book '${poem.bookName}'. Dive deep into his philosophical and poetic genius.`;
  const title = `${poem?.name} - ${poem.bookName}`;

  return {
    title: `${title} | allama-iqbal.com`,
    openGraph: {
      type: "article",
      title,
      description,
      siteName: "Iqbal's Poetry",
    },
    twitter: {
      card: "summary",
      title,
      description,
    },
    authors: { name: "Allama Iqbal" },
    keywords: `Iqbal, Poetry, ${poem.bookName}, ${poem?.name}, Allama Iqbal Poems, Urdu Poetry, Persian Poetry`,
    description,
  };
}
