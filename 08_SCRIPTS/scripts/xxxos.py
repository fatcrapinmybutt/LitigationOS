import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from docx import Document
import shutil
import csv
import argparse
from tqdm import tqdm
from colorama import init, Fore, Style
import fitz  # PyMuPDF for robust PDF text

# Initialize colorama
init(autoreset=True)

# ---------- USER-FRIENDLY PROMPTS ---------- #
def prompt_input(prompt, default=None):
    try:
        response = input(f"{Fore.GREEN}{prompt}{Style.RESET_ALL} [{default}]: ")
        return response.strip() or default
    except EOFError:
        return default

# ---------- ARGUMENT PARSING ---------- #
parser = argparse.ArgumentParser(
    description="FRED PRIME Evidence Scanner: scans files, performs OCR, tags exhibits."
)
parser.add_argument('-d', '--directory', help='Directory to scan (e.g., F:\\)', default=None)
parser.add_argument('-t', '--term', help='Search term (case-insensitive)', default=None)
parser.add_argument('-o', '--output', help='Output folder for exhibits', default=None)
parser.add_argument('-p', '--poppler', help='Path to Poppler bin', default=None)
args = parser.parse_args()

# ---------- CONFIGURATION ---------- #
SEARCH_DIR = args.directory or prompt_input("Enter directory to scan", "F:\\")
SEARCH_TERM = args.term or prompt_input("Enter search term", "custody violation")
OUTPUT_DIR = args.output or prompt_input("Enter output folder for exhibits", "F:\\FRED-PRIME-EVIDENCE")
POPPLER_PATH = args.poppler or prompt_input("Enter Poppler bin path", "F:\\popplar\\bin")
CSV_OUTPUT = os.path.join(os.getcwd(), 'match_results.csv')

# Validate directory
if not os.path.isdir(SEARCH_DIR):
    print(f"{Fore.RED}Error: Directory '{SEARCH_DIR}' does not exist.{Style.RESET_ALL}")
    exit(1)

# Display settings
def display_settings():
    print(Fore.CYAN + "\n=== Scanner Configuration ===")
    print(f"Directory    : {SEARCH_DIR}")
    print(f"Search term  : {SEARCH_TERM}")
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Poppler path : {POPPLER_PATH}")
    print(f"CSV output   : {CSV_OUTPUT}")
    print("="*32 + Style.RESET_ALL + "\n")

# ---------- GLOBALS ---------- #
results = []
exhibit_index = 0

# ---------- EXHIBIT LABEL UTILITY ---------- #
def next_exhibit_letter():
    global exhibit_index
    letter = chr(65 + exhibit_index)
    exhibit_index += 1
    return f"Exhibit {letter}"
