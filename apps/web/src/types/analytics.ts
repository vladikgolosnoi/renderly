export interface ProjectLeadStat {
  project_id: number;
  project_title: string;
  submissions: number;
  form_blocks: number;
  conversion_rate: number;
}

export interface LeadTimeseriesPoint {
  date: string;
  submissions: number;
}

export interface LeadTotals {
  submissions: number;
  projects: number;
  average_conversion: number;
}

export interface LeadAnalyticsResponse {
  summary: ProjectLeadStat[];
  timeseries: LeadTimeseriesPoint[];
  totals: LeadTotals;
  status_breakdown: Record<string, number>;
  generated_at: string;
}
