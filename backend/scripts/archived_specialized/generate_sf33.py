#!/usr/bin/env python3
"""
CLI Script: Generate SF33 Solicitation Forms and Complete Packages

Usage:
    # Generate SF33 only
    python scripts/generate_sf33.py --work-statement outputs/pws/performance_work_statement.md

    # Generate complete solicitation package
    python scripts/generate_sf33.py --package --work-statement outputs/pws/performance_work_statement.md

    # Generate for all document types
    python scripts/generate_sf33.py --all

    # Custom output directory
    python scripts/generate_sf33.py --work-statement outputs/pws/performance_work_statement.md \
                                     --output-dir outputs/solicitation/custom
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.sf33_generator_agent import SF33GeneratorAgent
from backend.agents.solicitation_package_orchestrator import SolicitationPackageOrchestrator


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate SF33 Solicitation Forms and Complete Packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate SF33 only
  %(prog)s --work-statement outputs/pws/performance_work_statement.md

  # Generate complete solicitation package
  %(prog)s --package --work-statement outputs/pws/performance_work_statement.md

  # Generate for all document types
  %(prog)s --all

  # Custom SF33 template
  %(prog)s --work-statement outputs/pws/performance_work_statement.md \\
           --sf33-template custom/SF33.pdf
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--work-statement',
        type=str,
        help='Path to work statement markdown file (PWS/SOO/SOW)'
    )
    input_group.add_argument(
        '--all',
        action='store_true',
        help='Generate SF33 for all available document types (PWS, SOO, SOW)'
    )

    # Output options
    parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs/solicitation',
        help='Output directory for generated files (default: outputs/solicitation)'
    )

    # Package options
    parser.add_argument(
        '--package',
        action='store_true',
        help='Generate complete solicitation package (SF33 + work statement + sections)'
    )

    # Template options
    parser.add_argument(
        '--sf33-template',
        type=str,
        default='data/documents/SF33.pdf',
        help='Path to SF33 PDF template (default: data/documents/SF33.pdf)'
    )

    # Verbosity
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress detailed output'
    )

    return parser.parse_args()


def generate_sf33_only(
    work_statement_path: str,
    output_dir: str,
    sf33_template: str,
    verbose: bool = True
) -> dict:
    """
    Generate SF33 form only

    Args:
        work_statement_path: Path to work statement markdown
        output_dir: Output directory
        sf33_template: Path to SF33 template
        verbose: Print progress

    Returns:
        Dictionary with results
    """
    # Initialize agent
    agent = SF33GeneratorAgent(sf33_template_path=sf33_template)

    # Determine output filename
    doc_name = Path(work_statement_path).stem
    output_path = f"{output_dir}/SF33_{doc_name}.pdf"

    # Generate
    result = agent.execute(
        work_statement_path=work_statement_path,
        output_path=output_path,
        verbose=verbose
    )

    return result


def generate_complete_package(
    work_statement_path: str,
    output_dir: str,
    sf33_template: str,
    verbose: bool = True
) -> dict:
    """
    Generate complete solicitation package

    Args:
        work_statement_path: Path to work statement markdown
        output_dir: Output directory
        sf33_template: Path to SF33 template
        verbose: Print progress

    Returns:
        Dictionary with results
    """
    # Initialize orchestrator
    orchestrator = SolicitationPackageOrchestrator(sf33_template_path=sf33_template)

    # Find corresponding PDF
    work_statement_pdf = work_statement_path.replace('.md', '.pdf')

    if not Path(work_statement_pdf).exists():
        return {
            'success': False,
            'error': f'PDF not found: {work_statement_pdf}'
        }

    # Determine output filename
    doc_name = Path(work_statement_path).stem
    output_path = f"{output_dir}/{doc_name}_package.pdf"

    # Build package
    result = orchestrator.build_complete_package(
        work_statement_md=work_statement_path,
        work_statement_pdf=work_statement_pdf,
        output_path=output_path,
        include_templates=False,  # L/M templates not implemented yet
        verbose=verbose
    )

    return result


def generate_all_documents(
    output_dir: str,
    sf33_template: str,
    package: bool = False,
    verbose: bool = True
) -> dict:
    """
    Generate SF33 for all available document types

    Args:
        output_dir: Output directory
        sf33_template: Path to SF33 template
        package: Generate complete packages
        verbose: Print progress

    Returns:
        Dictionary with results for all documents
    """
    documents = {
        'PWS': 'outputs/pws/performance_work_statement.md',
        'SOO': 'outputs/soo/statement_of_objectives.md',
        'SOW': 'outputs/sow/statement_of_work.md'
    }

    results = {}

    for doc_type, doc_path in documents.items():
        if not Path(doc_path).exists():
            print(f"\n⚠ Skipping {doc_type}: File not found ({doc_path})")
            continue

        print(f"\n{'='*70}")
        print(f"Processing {doc_type}")
        print(f"{'='*70}")

        if package:
            result = generate_complete_package(
                work_statement_path=doc_path,
                output_dir=output_dir,
                sf33_template=sf33_template,
                verbose=verbose
            )
        else:
            result = generate_sf33_only(
                work_statement_path=doc_path,
                output_dir=output_dir,
                sf33_template=sf33_template,
                verbose=verbose
            )

        results[doc_type] = result

    return results


def main():
    """Main entry point"""
    args = parse_arguments()

    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Verbose setting
    verbose = not args.quiet

    try:
        if args.all:
            # Generate for all document types
            results = generate_all_documents(
                output_dir=args.output_dir,
                sf33_template=args.sf33_template,
                package=args.package,
                verbose=verbose
            )

            # Summary
            print(f"\n\n{'='*70}")
            print("GENERATION SUMMARY")
            print(f"{'='*70}")

            for doc_type, result in results.items():
                if result.get('success'):
                    output_file = result.get('output_path', 'N/A')
                    print(f"  ✓ {doc_type}: {output_file}")
                else:
                    print(f"  ✗ {doc_type}: {result.get('error', 'Unknown error')}")

            print(f"{'='*70}\n")

        else:
            # Single document
            if not Path(args.work_statement).exists():
                print(f"✗ Error: File not found: {args.work_statement}")
                sys.exit(1)

            if args.package:
                result = generate_complete_package(
                    work_statement_path=args.work_statement,
                    output_dir=args.output_dir,
                    sf33_template=args.sf33_template,
                    verbose=verbose
                )
            else:
                result = generate_sf33_only(
                    work_statement_path=args.work_statement,
                    output_dir=args.output_dir,
                    sf33_template=args.sf33_template,
                    verbose=verbose
                )

            if not result.get('success'):
                print(f"\n✗ Generation failed: {result.get('error')}")
                sys.exit(1)

        print(f"\n✅ All operations completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
