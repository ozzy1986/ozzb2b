export type Category = {
  id: number;
  parent_id: number | null;
  slug: string;
  name: string;
  description: string | null;
  position: number;
};

export type CategoryTreeNode = Category & { children: CategoryTreeNode[] };

export type Country = { id: number; code: string; name: string; slug: string };
export type City = { id: number; country_id: number; name: string; slug: string; region: string | null };
export type LegalForm = { id: number; country_id: number | null; code: string; name: string; slug: string };

export type ProviderSummary = {
  id: string;
  slug: string;
  display_name: string;
  description: string | null;
  country: Country | null;
  city: City | null;
  legal_form: LegalForm | null;
  year_founded: number | null;
  employee_count_range: string | null;
  logo_url: string | null;
  categories: Category[];
  last_scraped_at: string | null;
};

export type ProviderDetail = ProviderSummary & {
  legal_name: string;
  website: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  registration_number: string | null;
  tax_id: string | null;
  source: string | null;
  source_url: string | null;
  status: string;
  is_claimed: boolean;
  created_at: string;
  updated_at: string;
};

export type FacetValue = { value: string; label: string; count: number };

export type ProviderFacets = {
  categories: FacetValue[];
  countries: FacetValue[];
  cities: FacetValue[];
  legal_forms: FacetValue[];
};

export type ProviderListResponse = {
  total: number;
  limit: number;
  offset: number;
  items: ProviderSummary[];
  facets: ProviderFacets | null;
};

export type UserPublic = {
  id: string;
  email: string;
  display_name: string | null;
  role: 'admin' | 'provider_owner' | 'client';
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  expires_at: string;
  user: UserPublic;
};

export type ConversationPeer = {
  provider_id: string;
  provider_slug: string;
  provider_display_name: string;
};

export type Conversation = {
  id: string;
  user_id: string;
  provider_id: string;
  last_message_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  peer: ConversationPeer | null;
};

export type ChatMessage = {
  id: string;
  conversation_id: string;
  sender_user_id: string | null;
  body: string;
  created_at: string;
};

export type WsTokenResponse = {
  token: string;
  expires_at: string;
  ws_url: string;
};

export type AnalyticsSummary = {
  days: number;
  items: { event_type: string; count: number }[];
};

export type TopQueries = {
  days: number;
  items: { query: string; count: number }[];
};

export type TopProviders = {
  days: number;
  items: {
    provider_id: string;
    display_name: string;
    slug: string;
    count: number;
  }[];
};
