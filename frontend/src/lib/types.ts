export type ClickEventType =
  | "phone"
  | "website"
  | "directions"
  | "detail"
  | "kakao_channel"
  | "mini_check_started"
  | "mini_check_completed"
  | "mini_check_result_viewed"
  | "mini_check_home_clicked"
  | "home_check_clicked"
  | "checklist_kakao_clicked"
  | "home_explore_selected"
  | "explore_check_clicked"
  | "check_explore_clicked";

export interface AcademySummary {
  id: number;
  name: string;
  address: string | null;
  phone: string | null;
  tagline: string | null;
  subjects: string[] | null;
  level_elementary: boolean | null;
  level_middle: boolean | null;
  level_high: boolean | null;
  class_small_group: boolean | null;
  class_group: boolean | null;
  class_one_on_one: boolean | null;
  curriculum_seonhaeng: boolean | null;
  curriculum_naesin: boolean | null;
  curriculum_suneung: boolean | null;
  shuttle_available: boolean | null;
  tuition_monthly_fee: number | null;
  last_verified_at: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface AcademyDetail extends AcademySummary {
  registration_number: string | null;
  website_url: string | null;
  blog_url: string | null;
  instagram_url: string | null;
  operating_hours: string | null;
  established_year: number | null;
  teacher_count: number | null;
  classroom_count: number | null;
  source_note: string | null;
}

export interface AcademyListResponse {
  items: AcademySummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ReviewEvidence {
  content: string;
  source: string | null;
  rating: number | null;
}

export type ConsultationIntent = "counsel_only" | "find_new_academy";

export interface ConsultationQuestion {
  topic: string;
  prompt: string;
}

export interface ConsultationRequest {
  grade: string;
  subject: string;
  school?: string;
  current_academy?: string;
  style_tags?: string[];
  concern: string;
  intent?: ConsultationIntent;
}

export interface ConsultationResponse {
  questions: ConsultationQuestion[];
  disclaimer: string;
  model: string;
  used_fallback: boolean;
}

export interface AiRecommendationItem {
  academy: AcademySummary;
  reason: string;
  score: number;
  evidence_reviews: ReviewEvidence[];
  matched_conditions: string[];
  unknown_conditions: string[];
  conflicts: string[];
}

export interface AiRecommendationResponse {
  query: string;
  parsed_intent: Record<string, unknown>;
  items: AiRecommendationItem[];
  relaxed: string[];
}

export interface CreatedResponse {
  id: number;
  created_at: string;
}

export interface ClickEventPayload {
  academy_id?: number | null;
  event: ClickEventType;
}

export interface WaitlistPayload {
  email?: string;
  kakao?: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
