import type { ResolvedPos } from "@tiptap/pm/model";
import type { SuggestionMatch, Trigger } from "@tiptap/suggestion";

export function findSuggestionMatch(config: Trigger): SuggestionMatch {
  const { $position } = config;

  const word = getWordAtCursor($position);
  if (!word) {
    return null;
  }

  return {
    range: {
      from: word.from,
      to: word.to,
    },
    query: word.word,
    text: word.word,
  };
}

function getWordAtCursor($position: ResolvedPos) {
  const textBefore = $position.nodeBefore ? $position.nodeBefore.text : "";
  const textAfter = $position.nodeAfter ? $position.nodeAfter.text : "";

  // Get the offset of the cursor within the current node
  const offsetInNode = $position.parentOffset;

  // Extract the word fragment before the cursor
  const beforeFragment = textBefore?.slice(0, offsetInNode).match(/\b\w+$/)?.[0] || "";

  // Extract the word fragment after the cursor
  const afterFragment = textAfter?.match(/^\w+\b/)?.[0] || "";

  // Combine both fragments to get the complete word
  const from = Math.max(textBefore?.lastIndexOf(beforeFragment) ?? 0, 0);
  const word = beforeFragment + afterFragment;

  if (!word) {
    return null;
  }

  return {
    word,
    from,
    to: from + word.length + 1,
  } as const;
}
