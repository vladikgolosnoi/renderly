import { describe, it, expect, beforeEach, vi } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import MarketplaceView from "../MarketplaceView.vue";
import api from "@/api/client";
import { useProjectStore } from "@/stores/project";
import type { ProjectDetail } from "@/types/blocks";

const push = vi.fn();

vi.mock("vue-router", () => ({
  useRouter: () => ({ push })
}));

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}));

const fallbackRouterLinkStub = {
  name: "RouterLink",
  props: ["to"],
  template: "<a><slot /></a>"
};

describe("MarketplaceView", () => {
  beforeEach(() => {
    push.mockReset();
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  const mountMarketplace = () =>
    mount(MarketplaceView, {
      global: {
        components: { RouterLink: fallbackRouterLinkStub }
      }
    });

  it("loads templates on mount and renders cards", async () => {
    const mockedGet = api.get as unknown as ReturnType<typeof vi.fn>;
    mockedGet.mockImplementation((url: string) => {
      if (url === "/templates") {
        return Promise.resolve({
          data: [
            {
              id: 1,
              title: "Faculty template",
              description: "Hero + intro",
              owner_name: "Admin",
              thumbnail_url: null,
              created_at: "2025-11-08T10:00:00Z"
            }
          ]
        });
      }
      if (url === "/templates/1/preview") {
        return Promise.resolve({ data: { html: "<html><body>preview</body></html>" } });
      }
      return Promise.resolve({ data: [] });
    });
    const wrapper = mountMarketplace();
    await flushPromises();

    expect(api.get).toHaveBeenCalledWith("/templates", undefined);
    expect(wrapper.text()).toContain("Faculty template");
  });

  it("imports template and redirects to editor", async () => {
    const store = useProjectStore();
    store.templates = [
      {
        id: 1,
        title: "Faculty template",
        description: "",
        owner_name: "Admin",
        thumbnail_url: null,
        created_at: "2025-11-08T10:00:00Z"
      }
    ];
    store.fetchTemplates = vi.fn().mockResolvedValue(undefined);
    store.importTemplate = vi.fn().mockResolvedValue({
      id: 42,
      title: "Clone",
      slug: "clone",
      description: "",
      status: "draft",
      theme: {},
      settings: {},
      visibility: "private",
      created_at: "",
      updated_at: "",
      blocks: []
    } as ProjectDetail);

    (api.get as unknown as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url === "/templates/1/preview") {
        return Promise.resolve({ data: { html: "<html></html>" } });
      }
      return Promise.resolve({ data: [] });
    });

    const wrapper = mountMarketplace();
    await flushPromises();

    await wrapper.find("button.use-template").trigger("click");
    expect(store.importTemplate).toHaveBeenCalledWith(1);
    expect(push).toHaveBeenCalledWith("/editor/42");
  });
});
