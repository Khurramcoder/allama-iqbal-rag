import { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import indexItems from "@/assets/new-index.json";
import { urNumberFormat } from "@/utils/intl";

interface Props {
  params: Promise<{ book: string }>;
}

export default async function Book({ params }: Props) {
  const { book: bookId } = await params;
  const bookIndex = indexItems.findIndex((book) => book.id === bookId);
  const book = indexItems[bookIndex];

  if (!book) {
    notFound();
  }

  return (
    <div
      className="mx-auto px-4 pb-10 text-center font-nastaliq leading-[2] sm:px-6 md:max-w-2xl md:px-4 lg:max-w-4xl lg:px-12"
      dir="rtl"
    >
      <div className="my-20 text-4xl">
        <span className="pe-4">({urNumberFormat.format(bookIndex + 1)})</span> {book.name}
      </div>
      {book.sections.map((section, sectionIndex) => (
        <section key={section.id} id={section.id} className="mt-10">
          {section.name && (
            <Link
              href={`#${section.slug}`}
              className="sticky top-0 block border-b border-gray-200 bg-white py-4 text-xl"
            >
              <span className="pe-4">({urNumberFormat.format(sectionIndex + 1)})</span> {section.name}
            </Link>
          )}

          {section.poems.map((poem, poemIndex) => (
            <Link
              key={poem.id}
              href={`/${book.slug}/${section.slug}/${poem.slug}`}
              className="text-baseline flex flex-col gap-x-3 gap-y-2 border-b border-dashed border-gray-300 px-4 py-4 text-start leading-[2] sm:flex-row sm:border-b-0"
            >
              <div className="flex gap-x-3">
                <div>({urNumberFormat.format(poemIndex + 1)})</div>
                <div>{poem.name}</div>
              </div>

              {(poem.nameAlt as any)?.en && (
                <>
                  <div className="hidden flex-1 border-b border-dashed border-gray-300 sm:block"></div>

                  <div dir="ltr" className="flex gap-x-2 text-start">
                    <div>{poemIndex + 1}.</div>
                    <div>{(poem.nameAlt as any)?.en}</div>
                  </div>
                </>
              )}
            </Link>
          ))}
        </section>
      ))}
    </div>
  );
}

export function generateStaticParams() {
  return indexItems.map((book) => ({ params: { book: book.id } }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { book: bookId } = await params;
  const bookIndex = indexItems.findIndex((book) => book.id === bookId);
  const book = indexItems[bookIndex];
  if (!book)
    return {
      title: "Allama Iqbal's Literary Works - Complete Collection",
      description:
        "Explore the complete collection of Allama Iqbal's literary masterpieces, including poetry, prose, and philosophical works. Access his books, translated versions, and more.",
    };

  return {
    title: `${book.name} by Allama Iqbal`,
    description: `Explore '${book.name}', one of the remarkable works of Allama Iqbal. Read the full text in ${book.language}. Published in ${book.year}`,
  };
}
