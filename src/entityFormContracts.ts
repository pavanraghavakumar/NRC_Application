export type FormField = {
  name: string;
  label: string;
  type?: 'text' | 'textarea' | 'select' | 'multi' | 'checkbox' | 'number' | 'rich';
  required?: boolean;
  max?: number;
  options?: string[];
  help?: string;
  conditional?: string;
  readOnly?: boolean;
};

const text = (name: string, label: string, required = false, max?: number): FormField => ({name, label, required, max});

export const entityFormContracts: Record<string, FormField[]> = {
  objectives: [text('objective', 'Objective', true, 4000), text('title', 'Title', false, 1000), text('sequence', 'Sequence'), text('goal_id', 'Strategic Goal'), text('fiscal_year_id', 'Fiscal Year')],
  strategies: [text('strategy', 'Strategy', true, 850), text('title', 'Title', false, 1000), text('sequence', 'Sequence', false, 100), text('goal_id', 'Strategic Goal'), text('objective_id', 'Strategic Objective'), text('fiscal_year_id', 'Fiscal Year')],
  'performance-goals': [text('performance_goal', 'Performance Goal', true, 1000), text('title', 'Title', true, 1000), text('sequence', 'Sequence', false, 100)],
  'fiscal-years': [text('fiscal_year', 'Fiscal Year', true, 100), text('start_date', 'Start'), text('end_date', 'End')],
  definitions: [text('title', 'Title', true, 100), text('identification_number', 'Identification Number'), {name:'description',label:'Description',type:'textarea',max:4000}, {name:'fiscal_year',label:'Fiscal Year',type:'number'}, text('office_id','Office'), text('goal_id','Strategic Goal'), text('objective_id','Strategic Objective'), text('strategy_id','Strategy')],
  'external-factors': [text('external_factor','External Factor',true,100), {name:'description',label:'Description',type:'textarea',required:true,max:4000}, text('affected_goal_id','Affected Goal'), text('fiscal_year_id','Fiscal Year',true)],
  offices: [text('office','Office',true,100), text('code','Code',false,100), text('prefix_code','Prefix Code',false,100), {name:'display_name',label:'Display Name',max:4000,help:'Calculated from Office',readOnly:true}],
  divisions: [text('name','Name',true,100), text('acronym','Acronym',false,100)],
  organizations: [text('name','Name',true,100)],
  'business-lines': [text('business_line','Business Line',true,850), text('br_code','B&R Code',false,100), text('prefix_code','Prefix Code',false,100), text('alternate_owner_id','Alternate Owner')],
  'product-lines': [text('product_line','Product Line',true,100), text('br_code','B&R Code',false,100), text('prefix_code','Prefix Code',false,100)],
  products: [text('product','Product',true,850), text('product_code','Product Code',false,100), {name:'internal_product_name',label:'Internal Product Name',max:4000,help:'Calculated from Product',readOnly:true}],
  'major-programs': [text('name','Name',true,100)],
  'contributing-programs': [text('name','Name',true,400)],
  'office-goals': [text('name','Name',true,100), text('office_id','Office',true)],
};

export function fieldsForEntity(slug: string): FormField[] {
  const fields = entityFormContracts[slug];
  if (!fields) throw new Error(`No form contract is registered for ${slug}`);
  return fields;
}

export function writablePayload(fields: FormField[], values: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(fields.filter(field => !field.readOnly).map(field => [field.name, values[field.name]]));
}
