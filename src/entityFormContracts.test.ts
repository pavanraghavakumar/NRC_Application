import {describe, expect, it} from 'vitest';
import {fieldsForEntity, writablePayload} from './entityFormContracts';

describe('shared entity form contracts', () => {
  it('renders and submits the Office API contract rather than generic fields', () => {
    const fields = fieldsForEntity('offices');
    expect(fields.map(field => field.name)).toEqual(['office', 'code', 'prefix_code', 'display_name']);
    expect(fields.find(field => field.name === 'office')).toMatchObject({label: 'Office', required: true});
    expect(writablePayload(fields, {office:'Office of Nuclear Reactor Regulation',code:'NRR',prefix_code:'OR',display_name:'computed'})).toEqual({office:'Office of Nuclear Reactor Regulation',code:'NRR',prefix_code:'OR'});
  });

  it.each([
    ['objectives',['objective','title','sequence','goal_id','fiscal_year_id']],
    ['strategies',['strategy','title','sequence','goal_id','objective_id','fiscal_year_id']],
    ['fiscal-years',['fiscal_year','start_date','end_date']],
    ['business-lines',['business_line','br_code','prefix_code','alternate_owner_id']],
    ['product-lines',['product_line','br_code','prefix_code']],
    ['products',['product','product_code','internal_product_name']],
    ['external-factors',['external_factor','description','affected_goal_id','fiscal_year_id']],
  ])('maps %s to documented API field names', (slug, expected) => {
    expect(fieldsForEntity(slug as string).map(field => field.name)).toEqual(expected);
  });
});
