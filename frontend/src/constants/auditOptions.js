export const agentSteps = [
  { name: 'Business Analyst', description: 'Extract and structure key business information' },
  { name: 'Strategic SWOT Analyst', description: 'Produce a detailed SWOT analysis' },
  { name: 'Pricing Strategy Consultant', description: 'Recommend the optimal pricing model' },
  { name: 'Growth Strategy Consultant', description: 'Create a detailed 90-day action plan' },
  { name: 'Business Report Writer', description: 'Assemble all research into a final report' },
];

export const initialFormState = {
  business_name: '',
  business_type: '',
  location: '',
  years_in_business: '',
  team_size: '',
  business_model: '',
  customer_type: '',
  monthly_revenue_range: '',
  customer_sources: [],
  current_marketing_channels: [],
  biggest_challenges: [],
  goals: [],
  additional_notes: '',
};

export const businessModelOptions = ['B2B', 'B2C', 'D2C', 'Marketplace', 'Other'];
export const customerTypeOptions = ['Retail', 'Enterprise', 'SME', 'Consumer', 'Mixed'];
export const revenueOptions = ['Under ₹1L', '₹1L–₹5L', '₹5L–₹20L', '₹20L–₹50L', 'Above ₹50L', 'Prefer not to say'];
export const tagOptions = ['Walk-ins', 'Instagram', 'Facebook', 'Google Ads', 'WhatsApp', 'Referrals', 'Website', 'LinkedIn', 'Cold Outreach', 'Other'];
export const challengeOptions = ['Low sales', 'High costs', 'Low repeat customers', 'Poor online presence', 'Hiring', 'Cash flow', 'Pricing', 'Competition', 'Operations', 'Marketing ROI'];
export const goalOptions = ['Increase revenue', 'Reduce costs', 'Expand to new markets', 'Build online presence', 'Improve retention', 'Launch new product', 'Raise funding', 'Automate operations'];
