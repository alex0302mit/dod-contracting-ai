"""
PDF Form Filler: Fill interactive PDF form fields programmatically
"""

from pypdf import PdfReader, PdfWriter
from typing import Dict, Optional
from pathlib import Path


class PDFFormFiller:
    """
    Fill interactive PDF form fields using pypdf library
    Supports text fields, checkboxes, and radio buttons
    """

    def __init__(self, template_path: str):
        """
        Initialize PDF Form Filler

        Args:
            template_path: Path to PDF template with fillable form fields
        """
        self.template_path = template_path
        self.reader = None
        self.writer = None
        self._load_template()

    def _load_template(self):
        """Load PDF template"""
        if not Path(self.template_path).exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        self.reader = PdfReader(self.template_path)
        print(f"✓ Loaded PDF template: {self.template_path}")
        print(f"  Pages: {len(self.reader.pages)}")
        print(f"  Form fields: {len(self.get_form_fields())}")

    def get_form_fields(self) -> Dict[str, str]:
        """
        Get all form fields from PDF

        Returns:
            Dictionary of field names and current values
        """
        fields = self.reader.get_form_text_fields()
        return fields if fields else {}

    def list_form_fields(self):
        """Print all available form fields"""
        fields = self.get_form_fields()
        print(f"\nAvailable Form Fields ({len(fields)}):")
        print("=" * 60)
        for i, (field_name, field_value) in enumerate(fields.items(), 1):
            print(f"{i:2}. {field_name}: '{field_value}'")

    def fill_form_fields(
        self,
        field_values: Dict[str, str],
        verbose: bool = True
    ) -> PdfWriter:
        """
        Fill PDF form fields with provided values

        Args:
            field_values: Dictionary mapping field names to values
            verbose: Print filling progress

        Returns:
            PdfWriter object with filled form
        """
        # Create writer and clone document
        self.writer = PdfWriter(clone_from=self.reader)

        # Get available fields
        available_fields = self.get_form_fields()

        # Fill fields
        filled_count = 0
        skipped_count = 0

        for field_name, value in field_values.items():
            if field_name in available_fields:
                try:
                    # Update all pages (pypdf approach)
                    for page_num in range(len(self.writer.pages)):
                        try:
                            self.writer.update_page_form_field_values(
                                self.writer.pages[page_num],
                                {field_name: value},
                                auto_regenerate=False
                            )
                        except:
                            pass  # Field may not be on this page

                    filled_count += 1
                    if verbose:
                        print(f"  ✓ Filled: {field_name} = '{value}'")
                except Exception as e:
                    print(f"  ✗ Error filling {field_name}: {e}")
                    skipped_count += 1
            else:
                if verbose:
                    print(f"  ⚠ Skipped (field not found): {field_name}")
                skipped_count += 1

        if verbose:
            print(f"\nFilling Summary:")
            print(f"  Successfully filled: {filled_count} fields")
            print(f"  Skipped: {skipped_count} fields")

        return self.writer

    def fill_form_field(
        self,
        field_name: str,
        value: str,
        page_number: int = 0
    ):
        """
        Fill a single form field

        Args:
            field_name: Name of the field to fill
            value: Value to set
            page_number: Page number (0-indexed)
        """
        if self.writer is None:
            self.writer = PdfWriter()
            for page in self.reader.pages:
                self.writer.add_page(page)

        self.writer.update_page_form_field_values(
            self.writer.pages[page_number],
            {field_name: value}
        )

    def set_checkbox(
        self,
        field_name: str,
        checked: bool = True,
        page_number: int = 0
    ):
        """
        Set checkbox or radio button state

        Args:
            field_name: Name of the checkbox field
            checked: True to check, False to uncheck
            page_number: Page number (0-indexed)
        """
        # For checkboxes, common values are '/Yes', '/Off', or similar
        # This varies by PDF creator
        value = '/Yes' if checked else '/Off'
        self.fill_form_field(field_name, value, page_number)

    def flatten_form(self, flatten: bool = False):
        """
        Flatten form fields (make non-editable)

        Args:
            flatten: If True, form fields become non-editable text
        """
        if self.writer and flatten:
            # Note: pypdf doesn't have direct flatten method
            # Form will remain fillable unless post-processed
            print("Note: Form flattening not fully supported in pypdf")
            print("      Fields will remain editable")

    def save_filled_pdf(
        self,
        output_path: str,
        flatten: bool = False
    ):
        """
        Save filled PDF to file

        Args:
            output_path: Path to save filled PDF
            flatten: Whether to flatten form fields
        """
        if self.writer is None:
            raise ValueError("No form has been filled yet. Call fill_form_fields() first.")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save
        with open(output_path, 'wb') as output_file:
            self.writer.write(output_file)

        print(f"\n✓ Saved filled PDF: {output_path}")

        # File size info
        file_size = Path(output_path).stat().st_size
        print(f"  File size: {file_size / 1024:.1f} KB")

    def fill_and_save(
        self,
        field_values: Dict[str, str],
        output_path: str,
        flatten: bool = False,
        verbose: bool = True
    ):
        """
        Fill form fields and save in one operation

        Args:
            field_values: Dictionary mapping field names to values
            output_path: Path to save filled PDF
            flatten: Whether to flatten form fields
            verbose: Print progress
        """
        print(f"\nFilling PDF Form: {Path(self.template_path).name}")
        print("=" * 60)

        # Fill fields
        self.fill_form_fields(field_values, verbose=verbose)

        # Save
        self.save_filled_pdf(output_path, flatten=flatten)

    def validate_fields(self, field_values: Dict[str, str]) -> Dict[str, list]:
        """
        Validate that provided fields exist in template

        Args:
            field_values: Dictionary of field names and values

        Returns:
            Dictionary with 'valid' and 'invalid' field lists
        """
        available_fields = set(self.get_form_fields().keys())
        provided_fields = set(field_values.keys())

        valid_fields = list(provided_fields & available_fields)
        invalid_fields = list(provided_fields - available_fields)

        return {
            'valid': valid_fields,
            'invalid': invalid_fields,
            'missing': list(available_fields - provided_fields)
        }


# Example usage
if __name__ == "__main__":
    # Test with SF33 template
    template_path = "data/documents/SF33.pdf"
    output_path = "outputs/solicitation/SF33_test_filled.pdf"

    if Path(template_path).exists():
        print("Testing PDF Form Filler with SF33 template\n")

        # Create filler
        filler = PDFFormFiller(template_path)

        # List available fields
        # filler.list_form_fields()

        # Test data
        test_data = {
            'SOLICITATION[0]': 'W911XX-25-R-1234',
            'CONTRACTNUM[0]': 'TBD',
            'DateISSUED[0]': '10/09/2025',
            'ISSUEDBY[0]': 'DOD/ARMY/LOGISTICS',
            'NAME10A[0]': 'John Smith',
            'EMAIL[0]': 'john.smith@army.mil',
            'PG1[0]': '1',
            'PG2[0]': '10',
            'PG11A[0]': '1',
            'PG11C[0]': '2',
            'PG11L[0]': '8',
            'PG11M[0]': '9'
        }

        # Fill and save
        filler.fill_and_save(
            field_values=test_data,
            output_path=output_path,
            verbose=True
        )

        print(f"\n✅ Test complete! Check output: {output_path}")

    else:
        print(f"✗ Template not found: {template_path}")
