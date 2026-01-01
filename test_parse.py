import re

with open("lotwreport_challenge.adi", 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

records = re.split(r'<eor>|<EOR>', text, flags=re.IGNORECASE)

entity_0_count = 0
monaco_80m = []

for record in records[:5000]:
    if not record.strip():
        continue
    
    fields = {}
    for match in re.finditer(r'<([^:>]+):(\d+)(?::([^>]+))?>([^<]*)', record, re.IGNORECASE):
        field_name = match.group(1).upper()
        field_value = match.group(4).strip()
        fields[field_name] = field_value
    
    dxcc = fields.get('DXCC', '')
    band = fields.get('BAND', '').upper()
    qsl = fields.get('QSL_RCVD', '').upper()
    
    if qsl == 'Y':
        if dxcc == '0':
            entity_0_count += 1
            print(f"Entity 0: Call={fields.get('CALL')}, Band={band}, Country={fields.get('COUNTRY')}")
        
        if dxcc == '3' and band == '80M':
            monaco_80m.append(fields.get('CALL'))

print(f"\nEntity 0 count: {entity_0_count}")
print(f"Monaco 80M count: {len(monaco_80m)}")