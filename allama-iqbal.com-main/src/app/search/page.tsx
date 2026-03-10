"use client";

import { ReactNode } from "react";
import { Hits, useInstantSearch } from "react-instantsearch";
import { InstantSearchNext } from "react-instantsearch-nextjs";

import { liteClient as algoliasearch } from "algoliasearch/lite";
import { type Hit as SearchHit } from "instantsearch.js";
import Link from "next/link";

import { SizeProvider, Verse } from "@/app/[book]/[section]/[poem]/components";
import SearchBox from "@/app/search/SearchBox";
import EmptySearchIllustration from "@/components/EmptySearchIllustration";

const searchClient = algoliasearch(process.env.NEXT_PUBLIC_ALGOLIA_APP_ID!, process.env.NEXT_PUBLIC_ALGOLIA_API_KEY!);

interface SearchHitItem {
  id: string;
  content: string;
  bookName: string;
  sectionName: string;
  poemName: string;
  paraName: string;
}

function SearchResult({ hit }: { hit: SearchHit<SearchHitItem> }) {
  const [bookId, sectionId, poemId, stanzaId] = hit.id.split("/");

  return (
    <div className="boder-gray-300 border-b px-4 py-4 font-mehr-nastaliq">
      <Link href={`/${bookId}/${sectionId}/${poemId}/?hash=cplt${stanzaId}`} className="text-2xl pb-4 block">
        <SizeProvider>
          {hit.content
            .split("\n")
            .map((line, i) => [i, line] as const)
            .map(([i, line]) => (
              <Verse content={line} key={i} />
            ))}
        </SizeProvider>
      </Link>
      <div className="flex items-center">
        <Link className="whitespace-nowrap px-2 transition hover:text-green-700" href={`/${bookId}`}>
          {hit.bookName}
        </Link>
        {hit.sectionName && (
          <>
            &#183;
            <Link
              className="whitespace-nowrap px-2 transition hover:text-green-700"
              href={`/${bookId}?hash=${sectionId}`}
            >
              {hit.sectionName}
            </Link>
          </>
        )}
        {hit.poemName && (
          <>
            &#183;
            <Link className="truncate px-2 transition hover:text-green-700" href={`/${bookId}/${sectionId}/${poemId}`}>
              {hit.poemName}
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

function EmptyQueryBoundary({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  const { indexUiState, results } = useInstantSearch();
  if (!indexUiState.query || results.hits.length === 0) {
    return (
      <>
        {fallback}
        <div hidden>{children}</div>
      </>
    );
  }

  return children;
}

function EmptyState() {
  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="flex flex-col items-center">
        <EmptySearchIllustration />
        <div className="mt-4">اقبال کے کلیات میں سے کتابیں، نظمیں یا اشعار تلاش کریں۔</div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <div
      className="mx-auto flex min-h-full flex-col px-4 py-10 font-nastaliq leading-[2] sm:px-6 md:max-w-2xl md:px-4 lg:max-w-4xl lg:px-12"
      dir="rtl"
    >
      <InstantSearchNext
        future={{ preserveSharedStateOnUnmount: true }}
        insights
        searchClient={searchClient}
        indexName="verses"
      >
        <SearchBox />
        <EmptyQueryBoundary fallback={<EmptyState />}>
          <Hits className="mt-10" hitComponent={SearchResult} />
        </EmptyQueryBoundary>
      </InstantSearchNext>
    </div>
  );
}
