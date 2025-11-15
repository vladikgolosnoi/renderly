import { describe, it, expect, beforeEach, vi } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import AnalyticsView from "../AnalyticsView.vue";
import api from "@/api/client";
import { useProjectStore } from "@/stores/project";
import type { Project } from "@/types/blocks";

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn()
  }
}));

const mockAnalytics = {
  summary: [
    {
      project_id: 1,
      project_title: "Lead Funnel",
      submissions: 5,
      form_blocks: 1,
      conversion_rate: 5
    }
  ],
  timeseries: [
    { date: "2025-11-07", submissions: 3 },
    { date: "2025-11-08", submissions: 2 }
  ],
  totals: {
    submissions: 5,
    projects: 1,
    average_conversion: 5
  },
  status_breakdown: {
    delivered: 4,
    failed: 1
  },
  generated_at: "2025-11-08T10:00:00Z"
};

describe("AnalyticsView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it("renders summary cards and table", async () => {
    const store = useProjectStore();
    store.projects = [
      {
        id: 1,
        title: "Lead Funnel",
        slug: "lead",
        description: "",
        status: "draft",
        theme: {},
        settings: {},
        visibility: "private",
        created_at: "",
        updated_at: ""
      } as Project
    ];
    store.fetchProjects = vi.fn().mockResolvedValue(undefined);
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockAnalytics });

    const wrapper = mount(AnalyticsView);
    await flushPromises();

    expect(api.get).toHaveBeenCalledWith("/analytics/leads", { params: {} });
    expect(wrapper.text()).toContain("Lead Funnel");
    expect(wrapper.findAll("table tbody tr")).toHaveLength(1);
    expect(wrapper.find(".summary-grid").exists()).toBe(true);
    expect(wrapper.find(".pulse").exists()).toBe(true);
  });
});
