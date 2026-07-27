#!/usr/bin/env bash
# Merge cohort gVCFs via GLnexus while skipping files that fail integrity checks.
# Recommended usage:
#   mamba activate clitools
#   ./merge_gvcfs.sh -i /data2/hb_gvcf/vcfs_out -o cohort.vcf.gz --config DeepVariantWGS

set -euo pipefail

detect_threads() {
  if command -v nproc >/dev/null 2>&1; then
    nproc
  elif command -v getconf >/dev/null 2>&1; then
    getconf _NPROCESSORS_ONLN
  else
    echo 4
  fi
}

DEFAULT_INPUT="/data1/vfagd2s_project/testdata/"
DEFAULT_OUTPUT="cohort_merged.vcf.gz"
DEFAULT_THREADS=$(detect_threads)
DEFAULT_GLNEXUS_CONFIG="DeepVariantWGS"

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  -i, --input-dir PATH       Directory that contains per-sample gVCF folders (default: $DEFAULT_INPUT)
  -o, --output FILE          Output multi-sample VCF path (default: $DEFAULT_OUTPUT)
  -t, --threads N            Number of threads for GLnexus/bcftools (default: $DEFAULT_THREADS)
  -c, --config NAME          GLnexus preset/config to use (default: $DEFAULT_GLNEXUS_CONFIG)
      --glnexus-dir PATH     Persistent GLnexus workspace directory (default: temp dir)
      --file-list FILE       Optional newline-delimited list of absolute gVCF paths to merge
  -v, --validation-mode MODE Validation strategy: full|gunzip|header|none (default: full)
  -f, --force                Overwrite existing output VCF if present
  -h, --help                 Show this help message

The script walks the input directory, validates every *.g.vcf.gz file,
records the list of healthy files, and finally emits a multi-sample VCF via GLnexus (piped through bcftools).
Run inside the mamba 'clitools' environment so that glnexus_cli, bcftools, and tabix are available.
EOF
}

info()  { printf '[INFO] %s\n' "$*"; }
warn()  { printf '[WARN] %s\n' "$*"; }
error() { printf '[ERROR] %s\n' "$*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || error "Required command '$1' is not available; activate the clitools mamba env."
}

validate_mode="full"
threads="$DEFAULT_THREADS"
force=false
input_dir="$DEFAULT_INPUT"
output_vcf="$DEFAULT_OUTPUT"
glnexus_config="$DEFAULT_GLNEXUS_CONFIG"
glnexus_dir=""
file_list_arg=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input-dir)
      [[ $# -ge 2 ]] || error "--input-dir requires a value"
      input_dir="$2"
      shift 2
      ;;
    -o|--output)
      [[ $# -ge 2 ]] || error "--output requires a value"
      output_vcf="$2"
      shift 2
      ;;
    -t|--threads)
      [[ $# -ge 2 ]] || error "--threads requires a value"
      threads="$2"
      shift 2
      ;;
    -c|--config)
      [[ $# -ge 2 ]] || error "--config requires a value"
      glnexus_config="$2"
      shift 2
      ;;
    --glnexus-dir)
      [[ $# -ge 2 ]] || error "--glnexus-dir requires a value"
      glnexus_dir="$2"
      shift 2
      ;;
    --file-list)
      [[ $# -ge 2 ]] || error "--file-list requires a value"
      file_list_arg="$2"
      shift 2
      ;;
    -v|--validation-mode)
      [[ $# -ge 2 ]] || error "--validation-mode requires a value"
      validate_mode="$(printf '%s' "$2" | tr 'A-Z' 'a-z')"
      shift 2
      ;;
    -f|--force)
      force=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      error "Unknown option: $1"
      ;;
  esac
done

case "$validate_mode" in
  full|gunzip|header|none) ;;
  *) error "Unsupported validation mode '$validate_mode' (choose from full|gunzip|header|none)";;
esac

[[ -n "$glnexus_config" ]] || error "GLnexus --config value cannot be empty"

if ! [[ "$threads" =~ ^[0-9]+$ && "$threads" -ge 1 ]]; then
  error "--threads must be a positive integer"
fi

require_cmd bcftools
require_cmd find
require_cmd sort
require_cmd gzip
require_cmd glnexus_cli

[[ -d "$input_dir" ]] || error "Input directory '$input_dir' does not exist"
input_dir=$(realpath "$input_dir")

if [[ -n "$file_list_arg" ]]; then
  [[ -f "$file_list_arg" ]] || error "--file-list '$file_list_arg' does not exist"
  file_list_arg=$(realpath "$file_list_arg")
fi

output_dir=$(dirname "$output_vcf")
mkdir -p "$output_dir"
output_dir=$(realpath "$output_dir")
output_vcf="$output_dir/$(basename "$output_vcf")"

if [[ -n "$glnexus_dir" ]]; then
  if [[ -e "$glnexus_dir" ]]; then
    if [[ "$force" == true ]]; then
      rm -rf "$glnexus_dir"
    else
      error "GLnexus workspace '$glnexus_dir' already exists. Use --force or provide a new path."
    fi
  fi
  mkdir -p "$(dirname "$glnexus_dir")"
  glnexus_dir=$(realpath "$glnexus_dir")
fi

if [[ -f "$output_vcf" && "$force" == false ]]; then
  error "Output file '$output_vcf' exists. Use --force to overwrite."
fi

tmp_dir=$(mktemp -d)
tmp_vcf="$tmp_dir/$(basename "$output_vcf").partial"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

report_prefix="$output_vcf"
if [[ "$output_vcf" == *.gz ]]; then
  report_prefix="${output_vcf%.gz}"
fi
valid_list="${report_prefix}.included_gvcfs.list"
skip_report="${report_prefix}.skipped_gvcfs.tsv"

: > "$valid_list"
skip_report_created=false

info "Collecting candidate gVCFs"
gvcf_candidates=()
if [[ -n "$file_list_arg" ]]; then
  info "Using --file-list $file_list_arg"
  mapfile -t gvcf_candidates < "$file_list_arg"
  filtered_candidates=()
  for line in "${gvcf_candidates[@]}"; do
    line=${line%$'\r'}
    [[ -z "$line" ]] && continue
    filtered_candidates+=("$line")
  done
  gvcf_candidates=("${filtered_candidates[@]}")
  unset filtered_candidates
else
  while IFS= read -r -d '' path; do
    gvcf_candidates+=("$path")
  done < <(find "$input_dir" -type f -name '*.g.vcf.gz' -print0)
fi

(( ${#gvcf_candidates[@]} > 0 )) || error "No .g.vcf.gz files found (check input directory or provided list)"

sorted_gvcfs=("${gvcf_candidates[@]}")
total_candidates=${#sorted_gvcfs[@]}

validation_error=''
validated=0
skipped=0
processed=0

# Stream the entire file (default mode) so we detect truncated/corrupted bgzip members early.
validate_gvcf() {
  local gvcf="$1"
  case "$validate_mode" in
    none)
      ;;
    header)
      if ! bcftools view -h "$gvcf" >/dev/null 2>&1; then
        validation_error="bcftools failed to read header"
        return 1
      fi
      ;;
    gunzip)
      if ! gunzip -t "$gvcf" >/dev/null 2>&1; then
        validation_error="gunzip integrity test failed"
        return 1
      fi
      ;;
    full)
      if ! bcftools view -Ou "$gvcf" >/dev/null 2>&1; then
        validation_error="bcftools could not stream file (likely corrupt block)"
        return 1
      fi
      ;;
  esac

  if [[ ! -f "${gvcf}.tbi" ]]; then
    if ! bcftools index --threads 1 -t "$gvcf" >/dev/null 2>&1; then
      validation_error="tabix indexing failed"
      return 1
    fi
  fi
  return 0
}

for gvcf in "${sorted_gvcfs[@]}"; do
  ((processed+=1))
  info "[$processed/$total_candidates] Checking $(basename "$gvcf")"
  validation_error="failed integrity check"
  if validate_gvcf "$gvcf"; then
    printf '%s\n' "$gvcf" >> "$valid_list"
    ((validated+=1))
  else
    warn "Skipping $gvcf :: $validation_error"
    if [[ "$skip_report_created" == false ]]; then
      printf "path\treason\n" > "$skip_report"
      skip_report_created=true
    fi
    printf '%s\t%s\n' "$gvcf" "$validation_error" >> "$skip_report"
    ((skipped+=1))
  fi
done

(( validated > 0 )) || error "No healthy gVCFs found. See $skip_report for details."

info "Validation finished: $validated passed, $skipped skipped."
info "Writing include list to $valid_list"
if [[ "$skip_report_created" == true ]]; then
  info "Troubled files recorded in $skip_report"
fi

info "Merging $validated gVCFs via GLnexus (config: $glnexus_config)"
glnexus_args=(
  --threads "$threads"
  --config "$glnexus_config"
  --list "$valid_list"
)
if [[ -n "$glnexus_dir" ]]; then
  glnexus_args+=( --dir "$glnexus_dir" )
fi

glnexus_cli "${glnexus_args[@]}" \
  | bcftools view --threads "$threads" -Oz -o "$tmp_vcf" -

mv "$tmp_vcf" "$output_vcf"
bcftools index --threads "$threads" -t -f "$output_vcf"

info "Merge complete: $output_vcf"
info "Tabix index written to ${output_vcf}.tbi"
