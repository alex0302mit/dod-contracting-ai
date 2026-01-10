import anthropic
import PyPDF2
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName
import re
from pathlib import Path
import markdown
import pdfkit

class MarketResearchFiller:
    def __init__(self, api_key):
        """Initialize with Anthropic API key"""
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def extract_pdf_text(self, pdf_path):
        """Extract text from PDF to understand structure"""
        reader = PyPDF2.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    
    def extract_form_fields(self, pdf_path):
        """Extract fillable form fields from PDF"""
        template = PdfReader(pdf_path)
        fields = {}
        
        for page in template.pages:
            if page.Annots:
                for annotation in page.Annots:
                    if annotation.T:  # Field has a name
                        field_name = annotation.T[1:-1]  # Remove parentheses
                        field_value = annotation.V if annotation.V else ""
                        fields[field_name] = {
                            'current_value': field_value,
                            'annotation': annotation
                        }
        
        return fields, template
    
    def generate_content_for_sections(self, project_info, template_text):
        """Generate content for all sections using Claude"""
        
        prompt = f"""You are filling out a government Market Research Report template.

CRITICAL RULES:
1. ONLY use facts from the provided project information
2. NEVER make up vendor names, statistics, or dates
3. Replace ALL vague words (several, many, some) with specific numbers
4. Add citations for every claim: "Per [source] dated [date]..."
5. Use neutral language - never favor specific vendors
6. Support all claims with evidence from project_info

If you don't have specific data for something, state: "Specific data to be determined during market research phase."

Project Information:
{self.format_project_info(project_info)}

Template Structure:
{template_text}

Please generate appropriate content for each section of this market research report. 
Format your response as a JSON object with the following structure:

{{
    "program_name": "...",
    "date": "MM/DD/YYYY",
    "prepared_by": "...",
    "program_office": "...",
    "author": "...",
    "report_date": "MM/DD/YYYY",
    "organization": "...",
    "report_title": "...",
    "product_service_description": "Detailed description including estimated dollar amount and period of performance...",
    "background": "Narrative on what this service will support, including past strategies if applicable...",
    "performance_requirements": "Critical performance requirements and any long-lead schedule items...",
    "market_research_conducted": "List of RFIs, industry days, and other research with dates and outcomes...",
    "contract_vehicles_considered": "Discussion of various contract vehicles considered...",
    "industry_capabilities": "List of potential vendors with contact info, capabilities assessment, and business size...",
    "small_business_opportunities": "Assessment of small business set-aside opportunities...",
    "commercial_opportunities": "Analysis of whether service meets FAR Part 2 definitions...",
    "conclusions_recommendations": "Summary with acquisition strategy recommendations, contract vehicles, and risks..."
}}

Make sure all content is:
- Professional and detailed
- Follows government contracting terminology
- Addresses all guidance points mentioned in the template
- Specific to the project information provided
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def generate_section_by_section(self, project_info, section_name, guidance):
        """Generate content for a specific section"""
        
        prompt = f"""Generate market research content for the following section. CRITICAL RULES:

1. ONLY use facts from this data: {self.format_project_info(project_info)}
2. NEVER make up vendor names, statistics, or dates
3. Replace ALL vague words (several, many, some) with specific numbers
4. Add citations for every claim: "Per [source] dated [date]..."
5. Use neutral language - never favor specific vendors
6. Support all claims with evidence from project_info

If you don't have specific data for something, state: "Specific data to be determined during market research phase."

Section: {section_name}

Guidance: {guidance}

Project Information:
{self.format_project_info(project_info)}

Provide detailed, professional content that addresses all points in the guidance.
Write 2-4 paragraphs of substantive content appropriate for a government contracting document.

IMPORTANT: Do NOT include the section title/heading in your response. Only provide the paragraph content.
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text.strip()

        # Remove any markdown headers that Claude might have added
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip lines that are just the section title as a header
            if line.strip().startswith('#'):
                continue
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()
    
    def fill_pdf_from_json(self, template, fields_data, output_path):
        """Fill PDF form fields with generated content"""
        
        for page in template.pages:
            if page.Annots:
                for annotation in page.Annots:
                    if annotation.T:
                        field_name = annotation.T[1:-1]  # Remove parentheses
                        
                        # Try to find matching content
                        for key, value in fields_data.items():
                            # Match field names (flexible matching)
                            if self.field_name_matches(field_name, key):
                                # Update the field value
                                annotation.update(
                                    PdfDict(V=value, AP=PdfDict())
                                )
                                break
        
        # Write the filled PDF
        PdfWriter().write(output_path, template)
        print(f"Filled PDF saved to: {output_path}")
    
    def field_name_matches(self, pdf_field, content_key):
        """Check if field name matches content key"""
        # Normalize strings for comparison
        pdf_field_norm = pdf_field.lower().replace('_', '').replace(' ', '')
        content_key_norm = content_key.lower().replace('_', '').replace(' ', '')
        return pdf_field_norm == content_key_norm or content_key_norm in pdf_field_norm
    
    def fill_pdf_by_text_replacement(self, pdf_path, project_info, output_path):
        """Alternative method: Replace text directly in PDF"""
        
        # Extract template text
        template_text = self.extract_pdf_text(pdf_path)
        
        # Generate all content
        print("Generating content with Claude...")
        generated_json = self.generate_content_for_sections(project_info, template_text)
        
        # Parse the JSON response
        import json
        try:
            # Extract JSON from response (may be wrapped in markdown)
            json_match = re.search(r'\{.*\}', generated_json, re.DOTALL)
            if json_match:
                content_dict = json.loads(json_match.group())
            else:
                print("Warning: Could not parse JSON response")
                return
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print("Raw response:", generated_json)
            return
        
        # Load template
        fields, template = self.extract_form_fields(pdf_path)
        
        print(f"Found {len(fields)} form fields in PDF")
        print("PDF Field names:", list(fields.keys()))
        print("\nGenerated content keys:", list(content_dict.keys()))
        print("\n--- Field Matching Debug ---")
        for pdf_field in fields.keys():
            matched = False
            for content_key in content_dict.keys():
                if self.field_name_matches(pdf_field, content_key):
                    print(f"✓ PDF field '{pdf_field}' matches content key '{content_key}'")
                    matched = True
                    break
            if not matched:
                print(f"✗ PDF field '{pdf_field}' has NO MATCH")
        print("--- End Debug ---\n")
        
        # Fill the fields
        self.fill_pdf_from_json(template, content_dict, output_path)
        
        return content_dict
    
    def fill_pdf_section_by_section(self, pdf_path, project_info, output_path):
        """Generate content section by section for better control"""
        
        # Define sections with their guidance
        sections = {
            "Product/Service Descriptions and Budget": """Include a description of the service to be addressed by this market research 
report. Information shall be provided to state current and projected service 
requirements to be addressed by this acquisition. Provide an estimated dollar amount 
and projected period of contract performance for this requirement.""",
            
            "Background": """Provide a short narrative on what this service shall be used to support. For 
follow on contracts, include information relative to the previous awards such as: 
past acquisition strategies supported, changes in the marketplace (suppliers, trends, technologies)""",
            
            "Performance Requirements": """State the critical performance requirements which the service must meet. 
Identify as appropriate any critical and long lead schedule items which will impact 
contract performance and delivery requirements.""",
            
            "Market Research Conducted": """List any market research conducted to include:
- Requests for Information (RFIs) / Sources Sought notices
- Individual correspondence with potential sources
- Industry days
- Discussions with other buyers for similar services""",
            
            "Industry Capabilities": """List of potential vendors and known sources of supply that could be solicited 
to provide the service required. Include location, point of contact information and an 
assessment of their potential capabilities to meet our requirements.""",
            
            "Small Business Opportunities": """Provide an assessment of the potential opportunities for small business set 
aside and direct award opportunities.""",
            
            "Commercial Opportunities": """Provide pertinent information that a contracting officer can use to conduct an
assessment as to whether the service meets the definitions of FAR Part 2 in terms of 
commercial items or non-developmental items.""",
            
            "Conclusions and Recommendations": """Summarize your data analysis with recommendations for: 
- Acquisition strategies to pursue
- List of potential contract vehicles
- Relevant risks to be considered"""
        }
        
        generated_content = {}
        
        print("Generating content section by section...")
        for section_name, guidance in sections.items():
            print(f"  - Generating: {section_name}")
            content = self.generate_section_by_section(project_info, section_name, guidance)
            generated_content[section_name] = content
        
        # Add basic metadata
        generated_content.update({
            "program_name": project_info.get("program_name", ""),
            "author": project_info.get("author", ""),
            "organization": project_info.get("organization", ""),
            "report_title": project_info.get("report_title", ""),
        })
        
        # Load and fill PDF
        fields, template = self.extract_form_fields(pdf_path)

        print(f"\nFound {len(fields)} form fields in PDF")
        print("PDF Field names:", list(fields.keys()))
        print("\nGenerated content keys:", list(generated_content.keys()))
        print("\n--- Field Matching Debug ---")
        for pdf_field in fields.keys():
            matched = False
            for content_key in generated_content.keys():
                if self.field_name_matches(pdf_field, content_key):
                    print(f"✓ PDF field '{pdf_field}' matches content key '{content_key}'")
                    matched = True
                    break
            if not matched:
                print(f"✗ PDF field '{pdf_field}' has NO MATCH")
        print("--- End Debug ---\n")

        self.fill_pdf_from_json(template, generated_content, output_path)
        
        return generated_content
    
    def format_project_info(self, info):
        """Format project info dictionary into readable text"""
        formatted = []
        for key, value in info.items():
            formatted_key = key.replace('_', ' ').title()
            formatted.append(f"- {formatted_key}: {value}")
        return "\n".join(formatted)
    
    def create_markdown_then_pdf(self, pdf_path, project_info, output_path):
        """
        Convert PDF to markdown, fill it, then convert back to PDF

        Args:
            pdf_path: Path to template PDF
            project_info: Dictionary with project details
            output_path: Path for output PDF
        """

        # Define sections with their guidance
        sections = {
            "Product/Service Description": """Include a description of the service to be addressed by this market research
report. Information shall be provided to state current and projected service
requirements to be addressed by this acquisition. Provide an estimated dollar amount
and projected period of contract performance for this requirement.""",

            "Background": """Provide a short narrative on what this service shall be used to support. For
follow on contracts, include information relative to the previous awards such as:
past acquisition strategies supported, changes in the marketplace (suppliers, trends, technologies)""",

            "Performance Requirements": """State the critical performance requirements which the service must meet.
Identify as appropriate any critical and long lead schedule items which will impact
contract performance and delivery requirements.""",

            "Market Research Conducted": """List any market research conducted to include:
- Requests for Information (RFIs) / Sources Sought notices
- Individual correspondence with potential sources
- Industry days
- Discussions with other buyers for similar services""",

            "Contract Vehicles Considered": """Discuss any consideration of various available contract vehicles.""",

            "Industry Capabilities": """List of potential vendors and known sources of supply that could be solicited
to provide the service required. Include location, point of contact information and an
assessment of their potential capabilities to meet our requirements.""",

            "Small Business Opportunities": """Provide an assessment of the potential opportunities for small business set
aside and direct award opportunities.""",

            "Commercial Opportunities": """Provide pertinent information that a contracting officer can use to conduct an
assessment as to whether the service meets the definitions of FAR Part 2 in terms of
commercial items or non-developmental items.""",

            "Conclusions and Recommendations": """Summarize your data analysis with recommendations for:
- Acquisition strategies to pursue
- List of potential contract vehicles
- Relevant risks to be considered"""
        }

        # Generate content for each section
        generated_content = {}
        print("Generating content section by section...")
        for section_name, guidance in sections.items():
            print(f"  - Generating: {section_name}")
            content = self.generate_section_by_section(project_info, section_name, guidance)
            generated_content[section_name] = content

        # Build markdown document
        markdown_content = f"""# Market Research Report

**Program Name:** {project_info.get('program_name', '')}

**Date:** {project_info.get('date', '10/01/2025')}

**Prepared by:** {project_info.get('author', '')}

**Program Office:** {project_info.get('organization', '')}

---

## Background Information

**Author:** {project_info.get('author', '')}

**Report Date:** {project_info.get('date', '10/01/2025')}

**Organization:** {project_info.get('organization', '')}

**Report Title:** {project_info.get('report_title', '')}

---

"""

        # Add each section
        for section_name, content in generated_content.items():
            markdown_content += f"## {section_name}\n\n{content}\n\n---\n\n"

        # Save markdown file for reference
        markdown_path = output_path.replace('.pdf', '.md')
        with open(markdown_path, 'w') as f:
            f.write(markdown_content)
        print(f"Markdown saved to: {markdown_path}")

        # Convert markdown to HTML
        html_content = markdown.markdown(markdown_content)

        # Add CSS styling for professional look
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Times New Roman', Times, serif;
                    max-width: 8.5in;
                    margin: 0.75in auto;
                    line-height: 1.6;
                    color: #333;
                }}
                h1 {{
                    text-align: center;
                    font-size: 24pt;
                    margin-bottom: 20px;
                }}
                h2 {{
                    font-size: 16pt;
                    margin-top: 20px;
                    margin-bottom: 10px;
                    border-bottom: 2px solid #333;
                }}
                p {{
                    text-align: justify;
                    margin-bottom: 12px;
                }}
                hr {{
                    border: none;
                    border-top: 1px solid #ccc;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Convert markdown to PDF using our custom converter
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            convert_markdown_to_pdf(markdown_path, output_path)
            print(f"PDF saved to: {output_path}")
        except Exception as e:
            print(f"Warning: Could not create PDF: {e}")
            print(f"However, markdown file was saved successfully: {markdown_path}")
            print("You can manually convert the markdown to PDF using any markdown editor.")

        return generated_content

    def create_filled_document(self, pdf_path, project_info, output_path, method="markdown"):
        """
        Main method to create filled document

        Args:
            pdf_path: Path to template PDF
            project_info: Dictionary with project details
            output_path: Path for output PDF
            method: "markdown" for markdown conversion, "json" for full document generation, "section" for section-by-section
        """

        if method == "markdown":
            return self.create_markdown_then_pdf(pdf_path, project_info, output_path)
        elif method == "section":
            return self.fill_pdf_section_by_section(pdf_path, project_info, output_path)
        else:
            return self.fill_pdf_by_text_replacement(pdf_path, project_info, output_path)


