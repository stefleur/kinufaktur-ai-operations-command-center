export const STATUSES = [
  { value: "incoming", label: "Incoming" },
  { value: "analyzing", label: "Analyzing" },
  { value: "planned", label: "Planned" },
  { value: "in_progress", label: "In Progress" },
  { value: "done", label: "Done" },
];

export const CATEGORIES = [
  "AI Automation",
  "Data",
  "Internal Operations",
  "Other",
];

export const PRIORITIES = ["Low", "Medium", "High"];

export function getStatusLabel(status) {
  return STATUSES.find((item) => item.value === status)?.label ?? status;
}
