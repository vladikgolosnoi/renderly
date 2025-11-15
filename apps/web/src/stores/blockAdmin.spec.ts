import { describe, it, expect, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useBlockAdminStore } from "./blockAdmin";
import api from "@/api/client";

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: [] })),
    post: vi.fn(() =>
      Promise.resolve({
        data: {
          id: 1,
          key: "hero",
          name: "Hero",
          category: "content",
          version: "1.0.0",
          schema: [],
          default_config: {}
        }
      })
    ),
    put: vi.fn(() =>
      Promise.resolve({
        data: {
          id: 1,
          key: "hero",
          name: "Hero updated",
          category: "content",
          version: "1.0.0",
          schema: [],
          default_config: {}
        }
      })
    ),
    delete: vi.fn(() => Promise.resolve({}))
  }
}));

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe("block admin store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("creates and updates block definitions", async () => {
    const store = useBlockAdminStore();
    const created = await store.createBlock({
      key: "hero",
      name: "Hero",
      category: "content",
      version: "1.0.0",
      schema: [],
      default_config: {}
    });
    expect(created.name).toBe("Hero");
    expect(mockedApi.post).toHaveBeenCalled();

    const updated = await store.updateBlock(1, { name: "Hero updated" });
    expect(updated.name).toBe("Hero updated");
    expect(store.blocks[0].name).toBe("Hero updated");
  });

  it("deletes block definition", async () => {
    const store = useBlockAdminStore();
    store.blocks = [
      {
        id: 1,
        key: "hero",
        name: "Hero",
        category: "content",
        version: "1.0.0",
        schema: [],
        default_config: {}
      }
    ];
    await store.deleteBlock(1);
    expect(store.blocks).toHaveLength(0);
    expect(mockedApi.delete).toHaveBeenCalledWith("/catalog/blocks/1");
  });
});
