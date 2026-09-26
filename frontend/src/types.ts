export interface KnowledgeBase {
  collection_id: string;
  collection_name: string;
  uploaded_at: string;
}

export interface Campaign {
  api_key?: string | null;
  allowed_origins: string[];
  campaign_id: string;
  campaign_name: string;
  campaign_description: string;
  start_date: string;
  end_date: string;
  status: string;
  target_audience: string;
  number_of_questions: number;
  branch_delta: number;
  collection_id: string;
  created_at: string;
  updated_at: string;
}

export interface CampaignCreate {
  campaign_name: string;
  campaign_description: string;
  start_date: string;
  end_date: string;
  status: string;
  target_audience: string;
  number_of_questions: number;
  branch_delta: number;
  collection_id: string;
  allowed_origins: string;
}

export interface QuestionSummary {
  question: string;
  summary: string;
}

export interface AnalysisReport {
  campaign_id: string;
  total_responses: number;
  question_summaries: QuestionSummary[];
  themes: string[];
  sentiment: string;
  insights: string[];
  generated_at: string;
}

export interface SurveyRequest {
  user_id: string;
  session_id?: string | null;
  campaign_id: string;
  answer?: string | null;
}

export interface SurveyResponse {
  session_id: string;
  session_number: number;
  question: string;
  question_count: number;
  survey_ended: boolean;
}
