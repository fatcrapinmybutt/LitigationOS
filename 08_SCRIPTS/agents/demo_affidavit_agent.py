#!/usr/bin/env python3
"""
Quick demo of Affidavit Agent capabilities
Shows claim analysis without reading the large master_index
"""

import sys
sys.path.insert(0, r'C:\Users\andre\LitigationOS\00_SYSTEM')

from affidavit_agent import (
    AffidavitDataReader, ChronologicalNarrativeBuilder,
    AffidavitWriter, ClaimAnalyzer
)

def main():
    print("=" * 80)
    print("AFFIDAVIT AGENT DEMO")
    print("=" * 80)
    print()
    
    # Initialize reader (skip master_index for speed)
    print("[1] Initializing data reader...")
    reader = AffidavitDataReader()
    del reader.databases['master_index']  # Skip 3.3GB database for demo
    
    # Read databases
    print("[2] Reading databases...")
    data = reader.read_all_databases()
    
    # Build narrative
    print("\n[3] Building chronological narrative...")
    builder = ChronologicalNarrativeBuilder(reader.events)
    chapters = builder.build_narrative()
    
    print(f"\nChapters created:")
    for chapter_num in sorted(chapters.keys()):
        event_count = len(chapters[chapter_num])
        chapter_title = builder.CHAPTERS[chapter_num]
        print(f"  Chapter {chapter_num}: {chapter_title} ({event_count} events)")
    
    # Show sample narrative
    if chapters:
        print("\n[4] Sample narrative excerpt:")
        print("-" * 80)
        first_chapter = min(chapters.keys())
        for event in chapters[first_chapter][:3]:  # First 3 events
            print(f"Date: {event.date}")
            print(f"  {event.description}")
            print()
    
    # Generate affidavit sample
    print("[5] Generating sample affidavit structure...")
    writer = AffidavitWriter(builder, reader.evidence)
    
    # Show what paragraphs would be generated
    paragraphs = writer._build_paragraphs('custody')
    print(f"Custody affidavit would have {len(paragraphs)} paragraphs")
    
    if paragraphs:
        print("\nFirst 3 paragraphs:")
        print("-" * 80)
        for para in paragraphs[:3]:
            print(f"{para.number}. {para.text}")
            print()
    
    # Analyze claims
    print("[6] Analyzing legal claims...")
    analyzer = ClaimAnalyzer(reader.events, reader.evidence)
    claims = analyzer.analyze_all_claims()
    
    print(f"\nTotal claims identified: {len(claims)}")
    print("\nClaims by defendant:")
    
    defendants = {}
    for claim in claims:
        if claim.defendant not in defendants:
            defendants[claim.defendant] = []
        defendants[claim.defendant].append(claim)
    
    for defendant, defendant_claims in defendants.items():
        print(f"\n  {defendant}:")
        for claim in defendant_claims[:3]:  # Show first 3
            print(f"    - {claim.claim_type.value.replace('_', ' ').title()}")
            print(f"      Strength: {claim.strength_score}/100")
            print(f"      Priority: {claim.filing_priority}")
            print(f"      Venue: {claim.recommended_venue.value}")
    
    # Summary
    print("\n" + "=" * 80)
    print("DEMO SUMMARY")
    print("=" * 80)
    print(f"Databases read: {len(reader.databases)}")
    print(f"Events extracted: {len(reader.events)}")
    print(f"Narrative chapters: {len(chapters)}")
    print(f"Claims identified: {len(claims)}")
    print()
    print("To generate full outputs, run:")
    print("  python affidavit_agent.py all")
    print()

if __name__ == "__main__":
    main()
