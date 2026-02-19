import csv
import io
import os
import sys

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

def generate_donguibogam_seed(input_file, output_file):
    # Mapping CSV columns to Table columns
    # Table columns: rep_code, rep_name, trad_code, trad_name, disease, disease_read, disease_alias, disease_alias_read, 
    # modern_disease, disease_src, disease_src_read, disease_src_year, disease_src_section, disease_content, 
    # prescription, prescription_read, prescription_modern, prescription_alias, presc_src, presc_src_read, 
    # presc_src_year, presc_src_section, indication, etc, food_type, ingredients, preparation, dosage
    
    columns = [
        'rep_code', 'rep_name', 'trad_code', 'trad_name', 'disease', 'disease_read', 'disease_alias', 'disease_alias_read',
        'modern_disease', 'disease_src', 'disease_src_read', 'disease_src_year', 'disease_src_section', 'disease_content',
        'prescription', 'prescription_read', 'prescription_modern', 'prescription_alias', 'presc_src', 'presc_src_read',
        'presc_src_year', 'presc_src_section', 'indication', 'etc', 'food_type', 'ingredients', 'preparation', 'dosage'
    ]

    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("-- Seed data for traditional_foods (Donguibogam)\n")
        outfile.write("TRUNCATE TABLE public.traditional_foods Restart IDENTITY;\n\n")
        
        batch_size = 1000
        batch_values = []
        
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            for i, row in enumerate(reader):
                values = []
                for col in columns:
                    val = row.get(col, '')
                    if val is None:
                        val = ''
                    # Escape single quotes for SQL
                    val = val.replace("'", "''")
                    # Handle newlines if necessary, though usually fine in quotes
                    values.append(f"'{val}'")
                
                batch_values.append(f"({', '.join(values)})")
                
                if len(batch_values) >= batch_size:
                    stmt = f"INSERT INTO public.traditional_foods ({', '.join(columns)}) VALUES\n"
                    stmt += ",\n".join(batch_values)
                    stmt += ";\n\n"
                    outfile.write(stmt)
                    batch_values = []
            
            # Flush remaining
            if batch_values:
                stmt = f"INSERT INTO public.traditional_foods ({', '.join(columns)}) VALUES\n"
                stmt += ",\n".join(batch_values)
                stmt += ";\n"
                outfile.write(stmt)

if __name__ == "__main__":
    base_dir = r"c:\AI\dev5"
    input_path = os.path.join(base_dir, "data", "info1.csv")
    output_path = os.path.join(base_dir, "supabase", "seed_donguibogam_data.sql")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generate_donguibogam_seed(input_path, output_path)
    print(f"Generated seed file: {output_path}")
