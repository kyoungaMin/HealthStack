"""
DBML to Mermaid ERD Converter with Section Support
Generates separate ERD diagrams for each logical section of the schema.
"""
import re
import os
import subprocess

# Define logical sections with their table names
SECTIONS = {
    "01_core_user": {
        "title": "Core User & Master Tables",
        "tables": ["auth_users", "user_profiles", "user_preferences", "foods_master", "disease_master", "catalog_drugs", "catalog_supplements"]
    },
    "02_intake_schedule": {
        "title": "Intake & Schedule Management",
        "tables": ["user_intake_items", "intake_schedules", "intake_logs", "user_push_tokens", "reports"]
    },
    "03_symptom_mapping": {
        "title": "Symptom & Ingredient Mapping",
        "tables": ["symptom_ingredient_map", "recipes", "symptom_recipe_map", "content_videos", "symptom_video_map", "ingredient_product_links"]
    },
    "04_input_session": {
        "title": "User Input Sessions & Prescriptions",
        "tables": ["user_input_sessions", "user_symptoms", "user_prescriptions", "user_prescription_drugs", "session_recommendation_results"]
    },
    "05_restaurant": {
        "title": "Restaurant Recommendations",
        "tables": ["restaurants", "restaurant_menus", "restaurant_search_templates", "restaurant_search_requests", "restaurant_search_results", "user_restaurant_favorites", "user_restaurant_visit_logs"]
    },
    "06_catalog_cache": {
        "title": "Catalog Codes & Cache",
        "tables": ["catalog_major_codes", "catalog_minor_codes", "youtube_cache", "commerce_cache"]
    },
    "07_tkm_mapping": {
        "title": "TKM (동의보감) Symptom Mapping",
        "tables": ["tkm_symptom_master", "tkm_to_modern_map"]
    },
    "08_pubmed": {
        "title": "PubMed & MeSH Integration",
        "tables": ["pubmed_papers", "pubmed_embeddings", "modern_to_mesh_map", "symptom_pubmed_map", "ingredient_pubmed_map", "interaction_facts"]
    },
    "09_billing": {
        "title": "Plans & Billing",
        "tables": ["plans", "subscriptions", "payments"]
    }
}

def parse_dbml(dbml_path):
    """Parse DBML file and extract all tables with columns and relationships."""
    with open(dbml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tables = {}
    relationships = []

    # Find Tables (handle nested braces for indexes)
    table_pattern = re.compile(r'Table\s+(\w+)\s*\{', re.MULTILINE)
    
    for match in table_pattern.finditer(content):
        table_name = match.group(1)
        start = match.end()
        
        # Find matching closing brace
        brace_count = 1
        end = start
        while brace_count > 0 and end < len(content):
            if content[end] == '{':
                brace_count += 1
            elif content[end] == '}':
                brace_count -= 1
            end += 1
        
        body = content[start:end-1]
        columns = []
        
        # Parse columns (skip indexes block)
        in_indexes = False
        for line in body.split('\n'):
            line = line.strip()
            if line.startswith('indexes'):
                in_indexes = True
                continue
            if in_indexes:
                if line.startswith('}'):
                    in_indexes = False
                continue
            if not line or line.startswith('Note:') or line.startswith('//'):
                continue
            
            # Column parser
            col_match = re.match(r'(\w+)\s+([\w\[\]]+)', line)
            if col_match:
                col_name = col_match.group(1)
                col_type = col_match.group(2).replace('[', '').replace(']', '')
                
                # Check for pk
                is_pk = '[pk' in line
                
                # Check for inline refs
                if 'ref:' in line:
                    ref_match = re.search(r'ref:\s*>\s*(\w+)\.(\w+)', line)
                    if ref_match:
                        target_table = ref_match.group(1)
                        relationships.append((table_name, target_table, col_name))
                
                pk_marker = " PK" if is_pk else ""
                # Mermaid ERD format: type name
                columns.append(f"{col_type} {col_name}{pk_marker}")
        
        tables[table_name] = columns

    return tables, relationships


def generate_section_mermaid(tables, relationships, section_tables, title):
    """Generate Mermaid ERD for a specific section."""
    section_set = set(section_tables)
    mermaid_lines = ["erDiagram"]
    
    # Add tables in this section
    for table in section_tables:
        if table in tables:
            mermaid_lines.append(f"    {table} {{")
            for col in tables[table]:
                mermaid_lines.append(f"        {col}")
            mermaid_lines.append("    }")
    
    # Add relationships within section
    seen_rels = set()
    for source, target, col in relationships:
        if source in section_set and target in section_set:
            rel_key = (source, target)
            if rel_key not in seen_rels:
                mermaid_lines.append(f"    {target} ||--o{{ {source} : has")
                seen_rels.add(rel_key)
        # Show external references
        elif source in section_set and target not in section_set:
            rel_key = (source, target)
            if rel_key not in seen_rels:
                mermaid_lines.append(f"    {target} ||--o{{ {source} : refs")
                seen_rels.add(rel_key)
    
    return "\n".join(mermaid_lines)


def main():
    dbml_path = 'docs/erd/schema.integrated.dbml'
    output_dir = 'docs/erd/sections'
    os.makedirs(output_dir, exist_ok=True)
    
    print("Parsing DBML...")
    tables, relationships = parse_dbml(dbml_path)
    print(f"Found {len(tables)} tables, {len(relationships)} relationships")
    
    # Generate combined index file
    index_lines = ["# Health Stack ERD - Section Index\n"]
    index_lines.append("> Auto-generated from `schema.integrated.dbml`\n\n")
    
    for section_id, section_info in SECTIONS.items():
        title = section_info["title"]
        section_tables = section_info["tables"]
        
        print(f"Generating {section_id}: {title}...")
        mermaid_content = generate_section_mermaid(tables, relationships, section_tables, title)
        
        # Write .mmd file (for image generation)
        mmd_path = os.path.join(output_dir, f"{section_id}.mmd")
        with open(mmd_path, 'w', encoding='utf-8') as f:
            f.write(mermaid_content)
        
        # Write .md file (for preview)
        md_path = os.path.join(output_dir, f"{section_id}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"**Tables**: {', '.join(section_tables)}\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_content)
            f.write("\n```\n")
        
        # Add to index
        index_lines.append(f"## {title}\n")
        index_lines.append(f"- **File**: [{section_id}.md](./{section_id}.md)\n")
        index_lines.append(f"- **Tables**: `{'`, `'.join(section_tables)}`\n\n")
    
    # Write index
    with open(os.path.join(output_dir, "README.md"), 'w', encoding='utf-8') as f:
        f.write("\n".join(index_lines))
    
    print(f"\nGenerated {len(SECTIONS)} section files in {output_dir}/")
    print("To generate PNG images, run:")
    print(f"  npx -y @mermaid-js/mermaid-cli -i {output_dir}/<section>.mmd -o {output_dir}/<section>.png")


if __name__ == "__main__":
    main()
