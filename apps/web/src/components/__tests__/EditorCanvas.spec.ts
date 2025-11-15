import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import EditorCanvas from "@/components/EditorCanvas.vue";

const paletteMime = "application/x-renderly-block";
const catalog = [
  {
    key: "hero",
    name: "Hero",
    category: "content",
    description: "",
    version: "1.0.0",
    schema: [{ key: "headline", label: "Headline", type: "text", required: true }],
    default_config: { headline: "Hello" }
  }
];

describe("EditorCanvas", () => {
  it("renders placeholder when empty", () => {
    const wrapper = mount(EditorCanvas, {
      props: { blocks: [], activeLocale: "ru", defaultLocale: "ru", catalog }
    });
    expect(wrapper.find(".empty").exists()).toBe(true);
  });

  it("emits select event", async () => {
    const wrapper = mount(EditorCanvas, {
      props: {
        blocks: [
          { id: 1, definition_key: "hero", order_index: 0, config: { headline: "Hi" } }
        ],
        activeLocale: "ru",
        defaultLocale: "ru",
        catalog
      }
    });
    await wrapper.find(".block").trigger("click");
    expect(wrapper.emitted("select")?.[0]).toEqual([1]);
  });

  it("emits insert event when palette block is dropped", async () => {
    const wrapper = mount(EditorCanvas, {
      props: { blocks: [], activeLocale: "ru", defaultLocale: "ru", catalog }
    });
    const dataTransfer = {
      types: [paletteMime],
      getData: (type: string) => (type === paletteMime ? "hero" : ""),
      setData: () => {},
      clearData: () => {}
    };
    await wrapper.find(".canvas").trigger("drop", {
      dataTransfer,
      preventDefault: () => {}
    });
    expect(wrapper.emitted("insert")?.[0]).toEqual([{ definitionKey: "hero", index: 0 }]);
  });
});
