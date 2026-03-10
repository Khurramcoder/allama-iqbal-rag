import { MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { Metadata } from "next";
import Link from "next/link";

import { urNumberFormat } from "@/utils/intl";

import indexItems from "../assets/new-index.json";

const languages: Record<string, string> = {
  ur: "اردو",
  fa: "فارسی",
};

export default async function Home() {
  return (
    <div
      className="mx-auto px-4 py-10 font-nastaliq leading-[2] sm:px-6 md:max-w-2xl md:px-4 lg:max-w-4xl lg:px-12"
      dir="rtl"
    >
      <div className="flex-1 text-center text-4xl leading-[2]">کلیات اقبال</div>

      <div className="mt-6 flex justify-center">
        <Link
          href="/search"
          className="relative flex w-64 items-center gap-x-4 rounded-md bg-gray-100 px-4 py-2.5 hover:bg-gray-200 focus:outline-none"
        >
          <MagnifyingGlassIcon className="absolute size-5 text-gray-600" />
          <div className="w-full text-center text-gray-600">تلاش کریں...</div>
        </Link>
      </div>

      <div className="mt-6">
        {indexItems.map((book, index) => (
          <Link key={book.id} href={`/${book.slug}`} className="py-4 block border-b border-dashed border-gray-300 pb-4">
            <div className="flex flex-col sm:flex-row justify-between items-stretch">
              <div className="flex flex-col items-start text-start mb-2 sm:mb-0 space-y-3">
                <div className="text-lg">
                  <span className="me-2">({urNumberFormat.format(index + 1)})</span>
                  {book.name}
                </div>
                <div className="text-sm text-gray-600 ">
                  {languages[book.language]} • {book.year}
                </div>
              </div>
              {book.nameAlt?.en && (
                <div dir="ltr" className="flex flex-col items-start text-start space-y-3">
                  <div className="text-lg">
                    <span className="me-2">{index + 1}. </span>
                    {book.nameAlt.en}
                  </div>
                  <div className="text-sm text-gray-600">
                  {book.language === "ur" ? "Urdu" : "Persian"} • {book.year}
                  </div>
                </div>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export const metadata: Metadata = {
  title: "Allama Iqbal's Literary Works - Complete Collection",
  description:
    "Explore the complete collection of Allama Iqbal's literary masterpieces, including poetry, prose, and philosophical works. Access his books, translated versions, and more.",
};
