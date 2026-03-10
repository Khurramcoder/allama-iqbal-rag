"use client";

import clsx from "clsx";
import { useCallback, useEffect, useMemo, useState } from "react";

import { autoUpdate, flip, offset, shift, useFloating } from "@floating-ui/react";
import { Portal } from "@radix-ui/react-portal";
import { SuggestionKeyDownProps } from "@tiptap/suggestion";
import { useAtomValue, useSetAtom } from "jotai";
import useSWR from "swr";

import { suggestionProps$, suggestionsKeydownHandler$ } from "./state";
import { useLocalStorage } from "@mantine/hooks";

const swrFetcher = (res: string) => fetch(res).then((res) => res.json());

export default function SuggestionList() {
  const suggestionProps = useAtomValue(suggestionProps$);
  const setKeydownHandler = useSetAtom(suggestionsKeydownHandler$);
  const [transLang] = useLocalStorage({
    key: "trans-lang",
    defaultValue: 'ur',
  })
  const [selectionIdx, setSelectionIdx] = useState(0);

  const clientRect = useMemo(() => suggestionProps?.clientRect?.(), [suggestionProps]);

  const { refs, floatingStyles } = useFloating({
    placement: "bottom-end",
    strategy: "fixed",
    whileElementsMounted: autoUpdate,
    middleware: [offset(10), flip(), shift()], // Adjust as needed
  });

  const { data } = useSWR(
    suggestionProps?.query &&
      `https://inputtools.google.com/request?text=${suggestionProps?.query}&itc=${transLang}-t-i0-und&num=4&cp=0&cs=1&ie=utf-8&oe=utf-8`,
    swrFetcher,
    {
      keepPreviousData: true,
      revalidateIfStale: false,
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    },
  );

  const items: string[] | undefined = data?.[1]?.[0]?.[1];

  useEffect(() => {
    if (clientRect) {
      refs.setReference({ getBoundingClientRect: () => clientRect });
    }
  }, [clientRect]);

  const keydownHandler = useCallback(
    (props: SuggestionKeyDownProps) => {
      const item = items?.[selectionIdx];
      const itemsLength = items?.length ?? 0;

      if (props.event.key === "ArrowDown" && itemsLength) {
        setSelectionIdx((idx) => (idx + 1) % itemsLength);
        return true;
      }

      if (props.event.key === "ArrowUp") {
        setSelectionIdx((idx) => (idx + (itemsLength - 1)) % itemsLength);
        return true;
      }

      if (props.event.key === "Enter" && item) {
        suggestionProps?.command({ ...suggestionProps, text: item });
        setSelectionIdx(0);
        return true;
      }

      return false;
    },
    [selectionIdx, suggestionProps, items],
  );

  useEffect(() => {
    setKeydownHandler(() => keydownHandler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keydownHandler]);

  if (!suggestionProps || !items) {
    return null;
  }

  return (
    <Portal>
      <div ref={refs.setFloating} style={{ ...floatingStyles }} tabIndex={0} className="z-50 w-48">
        <ul dir="rtl" data-suggestions-el="" className="rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
          {items.map((item, index) => (
            <li
              onClick={() => suggestionProps?.command({ ...suggestionProps, text: item })}
              tabIndex={0}
              key={item}
              className={clsx(
                `cursor-pointer px-4 py-2 font-mehr-nastaliq leading-relaxed`,
                selectionIdx === index ? "bg-gray-100" : "hover:bg-gray-100",
              )}
            >
              {item}
            </li>
          ))}
        </ul>
      </div>
    </Portal>
  );
}
