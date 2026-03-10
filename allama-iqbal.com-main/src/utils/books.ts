/* eslint-disable @typescript-eslint/no-unused-vars */
import indexItems from "@/assets/new-index.json";


export const flattenIndex = () => {
  const books = indexItems.map(
    ({ sections, ...book }) =>
      ({
        type: "book",
        ...book,
      }) as const,
  );

  const sectionsWithBook = indexItems.flatMap(({ sections, ...book }) =>
    sections.map(({ poems, ...section }) => ({ ...section, poems, book }) as const),
  );

  const poemsWithSection = sectionsWithBook.flatMap(({ poems, book, ...section }) =>
    poems.map(
      (poem) =>
        ({
          ...poem,
          section,
          book,
        }) as const,
    ),
  );

  const sections = sectionsWithBook
    .filter((e) => !!e.name)
    .map(
      ({ poems, ...section }) =>
        ({
          type: "section",
          ...section,
        }) as const,
    );

  const poems = poemsWithSection
    .filter((e) => !!e.name)
    .map(
      (poem) =>
        ({
          type: "poem",
          ...poem,
        }) as const,
    );

  return [...books, ...sections, ...poems] as (
    | (typeof books)[number]
    | (typeof poems)[number]
    | (typeof sections)[number]
  )[];
};

export function findAdjacentPoems(bookId: string, sectionId: string, poemId: string) {
  let prev = null;
  let next = null;

  const flattenedPoems = flattenIndex().filter((p) => p.type === "poem");
  type PoemType = Extract<(typeof flattenedPoems)[number], { type: "poem" }>;

  const currentIndex = flattenedPoems.findIndex(
    (poem) => poem.type === "poem" && poem.book.id === bookId && poem.section.id === sectionId && poem.id === poemId,
  );

  if (currentIndex > 0) {
    prev = flattenedPoems[currentIndex - 1];
  }

  if (currentIndex < flattenedPoems.length - 1) {
    next = flattenedPoems[currentIndex + 1];
  }

  return { prev, next } as { prev: PoemType; next: PoemType };
}
