import { describe, it, expect, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useProjectStore } from "./project";
import api from "@/api/client";

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: [] })),
    post: vi.fn(() => Promise.resolve({ data: { id: 1, name: "Tpl", slug: "tpl", palette: {} } })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({}))
  }
}));

const mockedApi = api as unknown as {
  put: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  get: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

const sampleBlocks = () => [
  { id: 1, definition_key: "hero", order_index: 0, config: {} },
  { id: 2, definition_key: "feature-grid", order_index: 1, config: {} },
  { id: 3, definition_key: "cta", order_index: 2, config: {} }
];

const sampleSettings = () => ({
  locales: { default_locale: "ru", locales: ["ru"] }
});

const sampleShareLink = () => ({
  id: 1,
  token: "share-token",
  label: "Preview",
  allow_comments: false,
  expires_at: new Date().toISOString(),
  created_at: new Date().toISOString(),
  created_by: 1,
  last_accessed_at: null,
  access_count: 0
});

describe("project store reorder & history", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("reorders blocks via drag & drop and persists order", async () => {
    const store = useProjectStore();
    store.current = {
      id: 99,
      title: "Test",
      slug: "test",
      description: null,
      status: "draft",
      theme: {},
      settings: sampleSettings(),
      visibility: "private",
      created_at: "",
      updated_at: "",
      blocks: sampleBlocks()
    };

    await store.reorderBlocks(0, 2);

    expect(store.current.blocks.map((b) => b.id)).toEqual([2, 3, 1]);
    expect(mockedApi.put).toHaveBeenCalledTimes(3);
    expect(store.canUndo).toBe(true);
  });

  it("undoes and redoes reorder steps", async () => {
    const store = useProjectStore();
    store.current = {
      id: 100,
      title: "History",
      slug: "history",
      description: null,
      status: "draft",
      theme: {},
      settings: sampleSettings(),
      visibility: "private",
      created_at: "",
      updated_at: "",
      blocks: sampleBlocks()
    };

    await store.reorderBlocks(2, 0);
    expect(store.current.blocks.map((b) => b.id)).toEqual([3, 1, 2]);

    store.undo();
    expect(store.current.blocks.map((b) => b.id)).toEqual([1, 2, 3]);

    store.redo();
    expect(store.current.blocks.map((b) => b.id)).toEqual([3, 1, 2]);
  });
});

describe("project store theme designer", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("updates theme and calls API", async () => {
    const store = useProjectStore();
    store.current = {
      id: 7,
      title: "Theme",
      slug: "theme",
      description: null,
      status: "draft",
      theme: { page_bg: "#ffffff" },
      settings: sampleSettings(),
      visibility: "private",
      created_at: "",
      updated_at: "",
      blocks: []
    };

    await store.updateTheme({ text_color: "#111111" });

    expect(store.current.theme?.text_color).toBe("#111111");
    expect(mockedApi.put).toHaveBeenCalledWith("/projects/7", {
      theme: expect.objectContaining({ text_color: "#111111" })
    });
  });

  it("saves theme template and updates list", async () => {
    const store = useProjectStore();
    store.current = {
      id: 8,
      title: "Theme Template",
      slug: "theme-tpl",
      description: null,
      status: "draft",
      theme: { page_bg: "#ffffff" },
      settings: sampleSettings(),
      visibility: "private",
      created_at: "",
      updated_at: "",
      blocks: []
    };
    mockedApi.post.mockResolvedValueOnce({
      data: { id: 10, name: "Corporate", slug: "corporate", palette: {} }
    });

    await store.saveThemeTemplate("Corporate");

    expect(store.themeTemplates.length).toBe(1);
    expect(store.themeTemplates[0].name).toBe("Corporate");
  });
});

describe("project share links", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("fetches existing share links", async () => {
    const store = useProjectStore();
    store.current = {
      id: 11,
      title: "Linkable",
      slug: "linkable",
      description: null,
      status: "draft",
      theme: {},
      settings: sampleSettings(),
      visibility: "private",
      created_at: "",
      updated_at: "",
      blocks: []
    };
    mockedApi.get.mockResolvedValueOnce({ data: [sampleShareLink()] });

    await store.fetchShareLinks();

    expect(mockedApi.get).toHaveBeenCalledWith("/projects/11/share-links");
    expect(store.shareLinks).toHaveLength(1);
  });

  it("creates and revokes a share link", async () => {
    const store = useProjectStore();
    store.current = {
      id: 15,
      title: "Shared",
      slug: "shared",
      description: null,
      status: "draft",
      theme: {},
      settings: sampleSettings(),
      visibility: "private",
      created_at: "",
      updated_at: "",
      blocks: []
    };
    mockedApi.post.mockResolvedValueOnce({ data: sampleShareLink() });

    await store.createShareLink({ label: "Preview", expiresInHours: 24 });

    expect(mockedApi.post).toHaveBeenCalledWith("/projects/15/share-links", {
      label: "Preview",
      expires_in_hours: 24,
      allow_comments: false
    });
    expect(store.shareLinks[0]?.token).toBe("share-token");

    mockedApi.delete.mockResolvedValueOnce({});
    await store.revokeShareLink(1);
    expect(mockedApi.delete).toHaveBeenCalledWith("/projects/15/share-links/1");
    expect(store.shareLinks).toHaveLength(0);
  });
});

describe("project sharing actions", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("updates project visibility", async () => {
    const store = useProjectStore();
    store.current = {
      id: 5,
      title: "Shared",
      slug: "shared",
      description: null,
      status: "draft",
      theme: {},
      settings: sampleSettings(),
      visibility: "private",
      created_at: "",
      updated_at: "",
      blocks: []
    };
    mockedApi.put.mockResolvedValueOnce({
      data: { ...store.current, visibility: "public" }
    });

    await store.updateVisibility("public");

    expect(mockedApi.put).toHaveBeenCalledWith("/projects/5", { visibility: "public" });
    expect(store.current?.visibility).toBe("public");
  });

  it("invites, updates and removes members", async () => {
    const store = useProjectStore();
    store.current = {
      id: 6,
      title: "Team",
      slug: "team",
      description: null,
      status: "draft",
      theme: {},
      settings: {},
      visibility: "shared",
      created_at: "",
      updated_at: "",
      blocks: []
    };
    mockedApi.post.mockResolvedValueOnce({
      data: {
        id: 10,
        project_id: 6,
        member_id: 42,
        email: "editor@example.com",
        role: "viewer",
        created_at: new Date().toISOString()
      }
    });

    await store.inviteMember("editor@example.com", "viewer");
    expect(store.members.length).toBe(1);

    mockedApi.put.mockResolvedValueOnce({
      data: {
        ...store.members[0],
        role: "editor"
      }
    });

    await store.updateMemberRole(10, "editor");
    expect(store.members[0].role).toBe("editor");

    await store.removeMember(10);
    expect(mockedApi.delete).toHaveBeenCalledWith("/projects/6/members/10");
    expect(store.members.length).toBe(0);
  });
});

describe("block creation extras", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("adds block with config override", async () => {
    const store = useProjectStore();
    store.blockCatalog = [
      {
        key: "hero",
        name: "Hero",
        category: "content",
        version: "1.0.0",
        schema: [],
        default_config: { headline: "Default" }
      }
    ];
    store.current = {
      id: 42,
      title: "Demo",
      slug: "demo",
      description: null,
      status: "draft",
      theme: {},
      settings: sampleSettings(),
      visibility: "private",
      created_at: "",
      updated_at: "",
      blocks: []
    };
    mockedApi.post.mockResolvedValueOnce({
      data: {
        ...store.current,
        blocks: [
          {
            id: 10,
            definition_key: "hero",
            order_index: 0,
            config: { headline: "Custom" },
            translations: {}
          }
        ]
      }
    });

    await store.addBlock("hero", undefined, { headline: "Custom" });

    expect(mockedApi.post).toHaveBeenCalledWith(`/projects/42/blocks`, {
      definition_key: "hero",
      order_index: 0,
      config: { headline: "Custom" },
      translations: {}
    });
  });

  it("adds block bundles sequentially", async () => {
    const store = useProjectStore();
    store.current = {
      id: 7,
      title: "Combo",
      slug: "combo",
      description: null,
      status: "draft",
      theme: {},
      settings: sampleSettings(),
      visibility: "private",
      created_at: "",
      updated_at: "",
      blocks: []
    };
    const addSpy = vi.spyOn(store, "addBlock").mockResolvedValue(undefined as never);

    await store.addBlockBundle(
      [
        { definitionKey: "hero", config: { headline: "Hero" } },
        { definitionKey: "form", config: { title: "Form" } }
      ],
      0
    );

    expect(addSpy).toHaveBeenNthCalledWith(1, "hero", 0, { headline: "Hero" });
    expect(addSpy).toHaveBeenNthCalledWith(2, "form", 1, { title: "Form" });
    addSpy.mockRestore();
  });
});
