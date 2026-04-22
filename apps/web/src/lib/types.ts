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
  last_scraped_at: string | null;
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
