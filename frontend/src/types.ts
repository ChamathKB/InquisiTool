export interface KnowledgeBase {
  collection_id: string;
  collection_name: string;
  uploaded_at: string;
}

export interface Campaign {
  campaign_id: string;
  campaign_name: string;
  campaign_description: string;
  start_date: string;
  end_date: string;
  status: string;
  target_audience: string;
  number_of_questions: number;
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
  collection_id: string;
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
