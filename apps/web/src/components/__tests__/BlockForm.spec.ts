import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import BlockForm from "../BlockForm.vue";
import type { BlockDefinition } from "@/types/blocks";

describe("BlockForm asset picker", () => {
  const catalog: BlockDefinition[] = [
    {
      key: "hero",
      name: "Hero",
      category: "content",
      version: "1.0.0",
      description: "",
      schema: [
        { key: "headline", label: "Заголовок", type: "text", required: true },
        { key: "image_url", label: "Изображение", type: "text", widget: "asset" }
      ],
      default_config: {}
    }
  ];

  it("emits request-asset when asset button is clicked", async () => {
    const wrapper = mount(BlockForm, {
      props: {
        block: {
          id: 1,
          definition_key: "hero",
          order_index: 0,
          config: { headline: "Test" }
        },
        catalog,
        locale: "ru",
        defaultLocale: "ru"
      }
    });

    const assetButton = wrapper.get('[data-test="asset-button-image_url"]');
    await assetButton.trigger("click");

    const events = wrapper.emitted("request-asset");
    expect(events).toBeTruthy();
    expect(events?.[0]?.[0]).toMatchObject({
      fieldKey: "image_url",
      blockId: 1,
      path: ["image_url"]
    });
  });
});
