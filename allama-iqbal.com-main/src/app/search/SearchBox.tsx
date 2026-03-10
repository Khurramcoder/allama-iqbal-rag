import { useEffect } from "react";
import { useSearchBox } from "react-instantsearch";

import { ChevronDownIcon } from "@heroicons/react/16/solid";
import { MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import * as Select from "@radix-ui/react-select";
import Document from "@tiptap/extension-document";
import Paragraph from "@tiptap/extension-paragraph";
import Placeholder from "@tiptap/extension-placeholder";
import Text from "@tiptap/extension-text";
import { EditorContent, useEditor } from "@tiptap/react";
import { useQueryState } from "nuqs";

import SuggestionList from "./SearchBox/SuggestionsList";
import { EditorContext } from "./SearchBox/context";
import { WordSuggestion } from "./SearchBox/suggestions-ext";
import "./searchbox.css";
import { useLocalStorage } from "@mantine/hooks";

const CustomDocument = Document.extend({
  content: "block",
});

export default function SearchBox() {
  const [inputValue, setInputValue] = useQueryState("q");
  const [transLang, setTransLang] = useLocalStorage({
    key: "trans-lang",
    defaultValue: 'ur',
  })
  const { refine } = useSearchBox({}, { $$widgetType: "ais.searchBox" });

  function setQuery(q: string) {
    setInputValue(q);
    refine(q);
  }

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      CustomDocument,
      Text,
      Paragraph,
      WordSuggestion,
      Placeholder.configure({
        placeholder: "کتابیں، نظمیں یا اشعار تلاش کریں",
      }),
    ],
    content: inputValue,
    onUpdate: ({ editor: ed }) => {
      setQuery(ed.getText());
    },
  });

  useEffect(() => {
    if (inputValue) {
      refine(inputValue);
    }
  }, []);

  return (
    <div className="relative">
      {editor?.isInitialized && (
        <>
          <div className="absolute inset-y-0 end-4 z-10 flex items-center">
            <Select.Root value={transLang} onValueChange={setTransLang}>
              <Select.Trigger className="flex items-center gap-x-px font-sans text-sm font-bold text-gray-800">
                <Select.Value />
                <Select.Icon>
                  <ChevronDownIcon className="size-4" />
                </Select.Icon>
              </Select.Trigger>

              <Select.Portal>
                <Select.Content className="z-50 overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg py-1">
                  <Select.Viewport>
                    <Select.Group>
                      <Select.Label className="font-sans text-sm text-gray-600 px-4 py-0.5 font-semibold">Transliteration Language</Select.Label>
                      <Select.Item
                        value="ur"
                        className="relative flex select-none items-center gap-x-2.5 px-4 py-2 data-[highlighted]:bg-gray-200 data-[highlighted]:outline-none [&>span]:text-sm [&>span]:font-semibold"
                      >
                        <Select.ItemText>UR</Select.ItemText>
                        <span>اردو</span>
                      </Select.Item>
                      <Select.Item
                        value="fa"
                        className="relative flex select-none items-center gap-x-2.5 px-4 py-2 data-[highlighted]:bg-gray-200 data-[highlighted]:outline-none [&>span]:text-sm [&>span]:font-semibold"
                      >
                        <Select.ItemText>FA</Select.ItemText>
                        <span>فارسی</span>
                      </Select.Item>
                    </Select.Group>
                  </Select.Viewport>
                </Select.Content>
              </Select.Portal>
            </Select.Root>
          </div>
          <div className="absolute inset-y-0 start-3 flex items-center">
            <MagnifyingGlassIcon className="size-5 text-gray-600" strokeWidth={1.7} />
          </div>
        </>
      )}

      <EditorContext.Provider value={editor}>
        <EditorContent dir="rtl" className="editor leading-[2]" editor={editor} />
        <SuggestionList />
      </EditorContext.Provider>
    </div>
  );
}
