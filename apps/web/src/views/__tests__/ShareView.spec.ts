import { describe, it, expect, beforeEach, vi } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import ShareView from "../ShareView.vue";
import api from "@/api/client";

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}));

vi.mock("vue-router", () => ({
  useRoute: () => ({
    params: { token: "preview-token" },
    fullPath: "/share/preview-token"
  })
}));

const mockSharePayload = {
  project: {
    id: 1,
    title: "Demo Landing",
    slug: "demo-landing",
    description: "",
    status: "draft",
    theme: {},
    settings: {},
    visibility: "private",
    created_at: "",
    updated_at: "2025-11-10T10:00:00Z"
  },
  html: "<html><body><h1>Demo</h1></body></html>",
  allow_comments: true,
  expires_at: null
};

describe("ShareView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders iframe preview when share is loaded", async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ data: mockSharePayload })
      .mockResolvedValueOnce({ data: [] });
    const wrapper = mount(ShareView);
    await flushPromises();

    expect(api.get).toHaveBeenNthCalledWith(1, "/shares/preview-token");
    expect(api.get).toHaveBeenNthCalledWith(2, "/shares/preview-token/comments");
    expect(wrapper.text()).toContain("Demo Landing");
    expect(wrapper.find("iframe").exists()).toBe(true);
  });

  it("shows error message when link expired", async () => {
    (api.get as unknown as ReturnType<typeof vi.fn>).mockRejectedValueOnce({ response: { status: 410 } });
    const wrapper = mount(ShareView);
    await flushPromises();

    expect(wrapper.text()).toContain("Ссылка больше не активна");
  });
});
