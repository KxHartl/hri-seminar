#!/usr/bin/env bash
# Build Documentation Script
# Usage: ./scripts/build-docs.sh [--clean] [--force] [--engine tectonic|latexmk] [--version v1]

clean=false
force=false
engine="auto"
version="v1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean)   clean=true; shift ;;
    --force)   force=true; shift ;;
    --engine)  engine="$2"; shift 2 ;;
    --version) version="$2"; shift 2 ;;
    *)         echo "Unknown option: $1"; exit 1 ;;
  esac
done

root_dir="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$root_dir"

echo "--- Building Documentation ---"

max_pages=12
dist_dir="${root_dir}/dist/${version}"
mkdir -p "$dist_dir"

# Detect engine
if [[ "$engine" == "auto" ]]; then
  if command -v tectonic &>/dev/null; then
    engine="tectonic"
  elif command -v latexmk &>/dev/null; then
    engine="latexmk"
  else
    echo "No LaTeX compiler found. Install Tectonic or TeX Live."
    exit 1
  fi
fi

echo "Engine: $engine | Version: $version"

tex_files=$(find docs -maxdepth 1 -name "*.tex" 2>/dev/null)

if [[ -z "$tex_files" ]]; then
  echo "No .tex files found in docs/."
  exit 0
fi

echo "$tex_files" | while read -r file; do
  echo "Building $(basename "$file")..."
  out_dir="$(dirname "$file")/build"

  if [[ "$force" == true && -d "$out_dir" ]]; then
    rm -rf "$out_dir"
    echo "  Force clean: build/ obrisan."
  fi

  mkdir -p "$out_dir"

  if [[ "$engine" == "tectonic" ]]; then
    tectonic -X compile "$file" --outdir "$out_dir" --keep-logs
  else
    latexmk -pdf -interaction=nonstopmode -shell-escape "-outdir=$out_dir" "$file"
  fi

  if [[ $? -eq 0 ]]; then
    pdf_name="$(basename "$file" .tex).pdf"
    if [[ -f "${out_dir}/${pdf_name}" ]]; then
      dist_name="$pdf_name"
      [[ "$pdf_name" == "main.pdf" ]] && dist_name="HRI_seminar_Kresimir_Hartl.pdf"
      cp "${out_dir}/${pdf_name}" "${dist_dir}/${dist_name}"
      echo "Done: $dist_name -> dist/${version}/"
    fi

    if [[ "$max_pages" -gt 0 ]]; then
      log_file="${out_dir}/$(basename "$file" .tex).log"
      if [[ -f "$log_file" ]]; then
        page_count=$(grep -o 'Output written on[^(]*([ ]*[0-9]* page' "$log_file" | grep -o '[0-9]*' | tail -1)
        if [[ -n "$page_count" ]]; then
          if [[ "$page_count" -gt "$max_pages" ]]; then
            echo "  UPOZORENJE: ${page_count} stranica (limit: ${max_pages})!"
          else
            echo "  Stranice: ${page_count} / ${max_pages}"
          fi
        fi
      fi
    fi
  else
    echo "FAILED: $(basename "$file")"
  fi
done

if [[ "$clean" == true ]]; then
  echo "Cleaning build directories..."
  find docs -type d -name "build" -exec rm -rf {} + 2>/dev/null
fi

echo "--- Build Finished ---"
