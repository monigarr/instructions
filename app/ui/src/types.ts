export type VerdictStatus = "match" | "mismatch" | "unable_to_verify" | "needs_review";

export interface FieldVerdict {
  field: string;
  status: VerdictStatus;
  application_value?: string | null;
  label_value?: string | null;
  reason: string;
  confidence: number;
}

export interface VerificationResult {
  label_id: string;
  verdicts: FieldVerdict[];
  summary: "passed" | "failed" | "needs_review";
  elapsed_ms: number;
  trace_id?: string;
  errors: string[];
}

export interface BatchProgress {
  batch_id: string;
  total: number;
  completed: number;
  passed: number;
  failed: number;
  needs_review: number;
  errors: number;
  finished: boolean;
  items: Array<{
    label_id: string;
    status: string;
    result?: VerificationResult;
    error?: string;
  }>;
}

export const DEFAULT_APPLICATION = {
  label_id: "single",
  brand_name: "OLD TOM DISTILLERY",
  class_type: "Kentucky Straight Bourbon Whiskey",
  alcohol_content: "45% Alc./Vol. (90 Proof)",
  net_contents: "750 mL",
  government_warning:
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
  bottler_producer_address: "Old Tom Distillery, Louisville, KY 40202",
  country_of_origin: "",
};

export interface SampleScenario {
  id: string;
  buttonLabel: string;
  imageHint: string;
  expectedHint: string;
  application: typeof DEFAULT_APPLICATION;
}

export const SAMPLE_SCENARIOS: SampleScenario[] = [
  {
    id: "old_tom_match",
    buttonLabel: "Load sample: Old Tom (pass)",
    imageHint: "Upload fixtures/labels/old_tom_match.png",
    expectedHint: "Expect: passed — all fields match",
    application: { ...DEFAULT_APPLICATION, label_id: "old_tom_match" },
  },
  {
    id: "warning_title_case",
    buttonLabel: "Load sample: Warning fail",
    imageHint: "Upload fixtures/labels/warning_title_case.png",
    expectedHint: "Expect: failed — government warning mismatch (Jenny Park)",
    application: {
      label_id: "warning_title_case",
      brand_name: "OLD TOM DISTILLERY",
      class_type: "Kentucky Straight Bourbon Whiskey",
      alcohol_content: "45% Alc./Vol. (90 Proof)",
      net_contents: "750 mL",
      government_warning:
        "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
      bottler_producer_address: "Old Tom Distillery, Louisville, KY 40202",
      country_of_origin: "",
    },
  },
  {
    id: "stones_throw_brand",
    buttonLabel: "Load sample: Brand nuance",
    imageHint: "Upload fixtures/labels/stones_throw_brand.png",
    expectedHint: "Expect: needs review — brand casing nuance (Dave Morrison)",
    application: {
      label_id: "stones_throw_brand",
      brand_name: "Stone's Throw",
      class_type: "Kentucky Straight Bourbon Whiskey",
      alcohol_content: "45% Alc./Vol. (90 Proof)",
      net_contents: "750 mL",
      government_warning:
        "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
      bottler_producer_address: "Old Tom Distillery, Louisville, KY 40202",
      country_of_origin: "",
    },
  },
];

export const FIELD_LABELS: Record<string, string> = {
  brand_name: "Brand Name",
  class_type: "Class / Type",
  alcohol_content: "Alcohol Content",
  net_contents: "Net Contents",
  government_warning: "Government Warning",
  bottler_producer_address: "Bottler / Producer Address",
  country_of_origin: "Country of Origin",
};
