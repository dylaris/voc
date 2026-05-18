import os
import sys
import json
from pathlib import Path

def merge_dict_files(input_dir=".", output_file="dict.json"):
    """
    Scan directory for JSONL files, extract word and translation, merge into single dict
    """
    merged = {}
    files_processed = 0

    # Find all JSON/JSONL files
    files = []
    for pattern in ["*.json", "*.jsonl"]:
        files.extend(Path(input_dir).glob(pattern))

    if not files:
        print(f"No JSON files found in {input_dir}")
        return merged

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        entry = json.loads(line)
                        word = entry.get('word', '').strip()
                        translation = entry.get('translation', [])

                        if word and translation:
                            # Take first translation if it's a list
                            if isinstance(translation, list) and translation:
                                translation_text = translation[0]
                            else:
                                translation_text = str(translation)

                            merged[word] = translation_text

                    except json.JSONDecodeError as e:
                        print(f"JSON decode error in {file_path} line {line_num}: {e}")

            files_processed += 1
            print(f"Processed: {file_path.name} ({len(merged)} entries so far)")

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Save merged dictionary
    if merged:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"\nSuccess! Merged {len(merged)} entries into {output_file}")
    else:
        print("No entries found to merge")

    return merged

if __name__ == "__main__":
    # Get directory from command line argument, default to current directory
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
        merge_dict_files(input_dir)
    else:
        print("usage: python merge.py <DIR>")
