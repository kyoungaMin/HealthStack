import csv
import io
import os
import sys

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

def generate_seed_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Sets to store unique values
        foods_master = {}
        disease_master = {}
        
        for row in reader:
            # 1. foods_master (Unique by rep_code)
            rep_code = row.get('rep_code')
            if rep_code and rep_code not in foods_master:
                foods_master[rep_code] = {
                    'rep_code': rep_code,
                    'rep_name': row.get('rep_name', ''),
                    'modern_name': row.get('trad_name', ''), # Fallback to trad_name as modern_name for now
                    'name_en': '',
                    'aliases': [],
                    'category': row.get('food_type', ''),
                    'nutrients': {}
                }
            
            # 2. disease_master (Unique by disease text)
            disease = row.get('disease')
            if disease and disease not in disease_master:
                disease_master[disease] = {
                    'disease': disease,
                    'disease_read': row.get('disease_read', ''),
                    'disease_alias': row.get('disease_alias', ''),
                    'disease_alias_read': row.get('disease_alias_read', ''),
                    'modern_disease': row.get('modern_disease', ''),
                    'modern_name_ko': row.get('modern_disease', ''), # Fallback
                    'name_en': '',
                    'icd10_code': '',
                    'category': '',
                    'aliases': []
                }

    # Generate SQL
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("-- Seed data for foods_master and disease_master\n\n")
        
        # foods_master
        f.write("-- foods_master\n")
        f.write("INSERT INTO public.foods_master (rep_code, rep_name, modern_name, name_en, aliases, category, nutrients) VALUES\n")
        
        food_values = []
        for code, data in foods_master.items():
            rep_name = data['rep_name'].replace("'", "''")
            modern_name = data['modern_name'].replace("'", "''")
            category = data['category'].replace("'", "''")
            val = f"('{code}', '{rep_name}', '{modern_name}', NULL, ARRAY[]::TEXT[], '{category}', '{{}}'::JSONB)"
            food_values.append(val)
            
        f.write(",\n".join(food_values))
        f.write("\nON CONFLICT (rep_code) DO NOTHING;\n\n")
        
        # disease_master
        f.write("-- disease_master\n")
        f.write("INSERT INTO public.disease_master (disease, disease_read, disease_alias, disease_alias_read, modern_disease, modern_name_ko, name_en, icd10_code, category, aliases) VALUES\n")
        
        disease_values = []
        for name, data in disease_master.items():
            disease = data['disease'].replace("'", "''")
            if not disease: continue
            
            disease_read = data['disease_read'].replace("'", "''")
            disease_alias = data['disease_alias'].replace("'", "''")
            disease_alias_read = data['disease_alias_read'].replace("'", "''")
            modern_disease = data['modern_disease'].replace("'", "''")
            modern_name_ko = data['modern_name_ko'].replace("'", "''")
            
            val = f"('{disease}', '{disease_read}', '{disease_alias}', '{disease_alias_read}', '{modern_disease}', '{modern_name_ko}', NULL, NULL, NULL, ARRAY[]::TEXT[])"
            disease_values.append(val)
            
        f.write(",\n".join(disease_values))
        f.write("\nON CONFLICT (disease) DO NOTHING;\n")

# Run generation
if __name__ == "__main__":
    base_dir = r"c:\AI\dev5"
    input_path = os.path.join(base_dir, "data", "info1.csv")
    output_path = os.path.join(base_dir, "supabase", "seed_master_data.sql")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generate_seed_data(input_path, output_path)
    print(f"Generated seed file: {output_path}")
