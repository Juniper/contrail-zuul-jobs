#!/usr/bin/env bash

# Exit on error immediately
set -e

# Report failures of any stage in pipeline.
set -o pipefail

# On control-C or ERROR, terminate all sub-processes
trap 'pkill $PPID' INT ERR

# Get absolute path of script
script_name="$(basename "$0")"
script_dir="$(readlink -m "$(dirname "$0")")"
# Directory where the repos are
#base_dir="$(readlink -m "$script_dir/../../contrail")"
base_dir="."
# Log base directory
log_base_dir=/var/tmp

# For formatting
bold=$(tput bold)
normal=$(tput sgr0)




# Parse arguments

OPTS=$(getopt -o h --long chdir:,repos:,all,report:,help -n parse-options -- "$@")
eval set -- "$OPTS"

# Set defaults
declare -a repo_paths=(all)
default_report=/dev/stdout
report="$default_report"

while true; do
    case "$1" in
        --chdir) base_dir="$2"; shift 2;;
        --repos) repo_paths=("${2//,/ }"); shift 2;;
        --report) report="$2"; shift 2;;
        --help|-h) help | more; exit 0;;
        --) shift; break;;
        *) echo "Unexpected argument: $1" >&2 && help && exit 1
    esac
done

# Repo tool must be run from directory with .repo/manifest.xml
cd "$base_dir"

# Replace "all" with actual repo names
declare -A all_repos
# convert "repo/path : repo-name" to "repo/path:repo-name"
for repo in $(repo list | sed 's/ : /:/'); do   
    # add each path to repo hash, and save the repo name
    all_repos[${repo%:*}]=${repo#*:}
done
[[ "${repo_paths[*]}" != all ]] || repo_paths=("${!all_repos[@]}")

# Create a log file for a repo, and a given stage (e.g.- caniusepython3, modernize, futurize)
logfile() {
    module_path=$1
    stage=${2:-caniusepython3}
    # Save output for debugging.
    log_file=${log_base_dir}/${module_path}.${stage}.log
    mkdir -p "$(dirname "$log_file")"
    echo "$log_file"
}


# Determine if a repo has blocking dependencies to using python3
# Return non-zero status if incompatibility detected.
module_caniusepython3() {
    module_path="$1"
    [[ "$module_path" ]] || return 1 

    # Save output for debugging.
    log_file=$(logfile "$module_path")

    # Find all requirements.txt files.
    requirements=()
    mapfile -t requirements < <(find "$PWD/$module_path" -name '*requirements.txt')

    # Do not test module with no requirements.txt
    if [[ ! ${#requirements[@]} -gt 0 ]]; then
        printf "MODULE @%s has no *requirements.txt.  Skipping...\n\n" "$module_path"
        return 0
    fi

    printf "TESTING MODULE: @%s...\n\n" "$module_path" >&2
    caniusepython3 --verbose --requirements "${requirements[@]}" >"$log_file" 2>&1

    # Look for errors or warnings that are not filtered out.
    # Don't worry about entries in requirements.txt that have relative pathing since they are internal.
    # Filter out everything that's ignored.
    if grep -E '^\[(ERROR|WARNING)\] ' "$log_file" | grep -v -F " Skipping '../" | grep -v -f "$modules_ignore_file"; then
        printf "MODULE @%s FAILED.\n" "$module_path"
        cat "$log_file"
        # If this happens, there may be unparsable output resulting in an erroneous log.
        # Simply exit the script in this case.
        exit 1
    fi

    # Report results
    sed -ne '/^Finding and checking dependencies/,$ p' "$log_file"

    # Fail if we have some projects yet to transition.
    grep -q -F 'You have 0 projects blocking you from using Python 3!' "$log_file" || (echo && return 1)
}


# Print the blocking modules from the log file
logfile_blockers() {
    module_path=$1
    log_file=$(logfile "$module_path")
    [[ -r "$log_file" ]] || return 0
    sed -ne '/^Finding and checking dependencies/,$ p' "$log_file" | sed -ne '/^  / p' | cut -d' ' -f3
}


# Report results in an XML document.
report() {
    printf '<xml version="1.0">'
    for repo_path in "${repo_paths[@]}"; do
        printf '\n  <repo name="%s" path=\"%s">' "${all_repos[$repo_path]}" "$repo_path"
        module_found=
        for module_path in ${repo_module_paths[$repo_path]}; do
            module_found=1
            module_name=${path_to_module[$module_path]}
            printf '\n    <module name="%s" path="%s" python3-support="%s">' "$module_name" "$module_path" "${python3_modules[$module_path]}"
            blockers=()
            mapfile -t blockers < <(logfile_blockers "$module_path")
            if [[ ${#blockers[0]} -eq 0 ]]; then
                printf "</module>"
            else
                printf '\n      <blocker module="%s"/>' "${blockers[@]}"
                printf '\n    </module>'
            fi
        done
        if [[ $module_found ]]; then
            printf '\n  </repo>'
        else
            printf '</repo>'
        fi
    done
    printf '\n</xml>\n'
    return 0
}


# Path to module
declare -A path_to_module
# Converted modules
declare -A python3_modules
# Set of modules to ignore
declare -A modules_to_ignore
# Set of modules paths defined in a repo
declare -A repo_module_paths

# Overall return code
ret=0

# Iterate through all the repos and look for python modules
for repo_path in "${!all_repos[@]}"; do
    declare -a internal_modules=()
    declare -a internal_module_paths=()
    # Every python modules has a setup.py
    setup_py_files=()
    mapfile -t setup_py_files < <(find "$repo_path" -name setup.py)
    for setup_py in "${setup_py_files[@]}"; do
        # Look for the module name
        module=$(sed -n -e '/^[[:space:]]*name=/ p' "$setup_py" 2>/dev/null | sed -e "s:\":':g" | cut -d\' -f2 || true)
        [[ "$module" ]] || continue
        # Get the path to the module, and add it to an associative array
        module_path=$(dirname "$setup_py")
        path_to_module["$module_path"]=$module
        # Keep a list of internal modules and paths for this repo
        internal_modules+=("$module")
        internal_module_paths+=("$module_path")
        # Check if this module is already converted to python3
        python3_module=no
        if grep -q "'Programming Language :: Python :: 3'" "$setup_py"; then python3_module=yes; fi
        python3_modules["$module_path"]=$python3_module
    done
    # Keep a list of all the internal modules used by this repo
    repo_module_paths["$repo_path"]="${internal_module_paths[*]}"
    for module in "${internal_modules[@]}"; do
        modules_to_ignore[$module]=1
    done
done

# Create a regex file of (internal) modules to ignore
modules_ignore_file="$log_base_dir"/modules.ignore
printf "[ /,]%q[ /,].*[Nn]ot [Ff]ound\n" "${!modules_to_ignore[@]}" >"$modules_ignore_file"
# Also ignore components pulled in by path directly
for internal_module_path in "${!modules_to_ignore[@]}" "${!path_to_module[@]}"; do
    module_base_path=$(basename "$internal_module_path")
    printf ' problem fetching %s, \n' "$module_base_path" >>"$modules_ignore_file"
done

# For each of the repos requested, for each module in the repo, perform the analysis
for repo_path in "${repo_paths[@]}"; do
    for module_path in ${repo_module_paths[$repo_path]}; do
        # Verify if we can use Python3
        if ! module_caniusepython3 "$module_path"; then
            ret=1
        fi
    done
done


# Generate XML Report if requested
printf "\nREPORT: %s\n\n" "$report"
report >"$report"

# Finally, report overall status.
exit $ret