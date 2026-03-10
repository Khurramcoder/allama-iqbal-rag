import { type SuggestionKeyDownProps, type SuggestionProps } from "@tiptap/suggestion";
import { atom } from "jotai";

export const suggestionProps$ = atom<SuggestionProps | null>(null);
export const suggestionsKeydownHandler$ = atom<((props: SuggestionKeyDownProps) => boolean) | null>(null);
