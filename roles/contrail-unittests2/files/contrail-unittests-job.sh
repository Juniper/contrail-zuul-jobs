#!/usr/bin/env bash

set -o pipefail

CONTRAIL_SOURCES="$WORKSPACE/contrail-$UPSTREAM_VERSION"
REPO_BIN="$WORKSPACE/repo"

function pytest_to_file() {
  _PYTEST_XTRACE=$(set +o | grep xtrace)
  set -x

  local pattern=$1
  if [ -e $CONTRAIL_SOURCES/.repo ]; then
      $REPO_BIN grep -l $bare_name
  else
      # if we are not running under repo, run grep
      # while excluding build/ .git/ and third_party/.
      (cd $CONTRAIL_SOURCES && ack-grep --ignore-dir={build/,third_party/,debian/} -l "$pattern")
  fi

  $_PYTEST_XTRACE
}

function ci_exit() {
    exit_code=$1
    if [ -z $exit_code ]; then
        exit_code=0
    fi
    archive_failed_test_logs
    JENKINS_JOB_N=$(basename "$JOB_URL")
    if [ "$exit_code" == "0" ]; then
        #rm -rf $WORKSPACE/* $WORKSPACE/.* 2>/dev/null
        echo Success
    else
        # Leave the workspace intact.
        echo Exit with failed code $exit_code
    fi
    exit $exit_code
}

if [ -f "$SKIP_JOBS" ]; then
    echo Jobs skipped due to presence of file $SKIP_JOBS
    ci_exit
fi

function archive_failed_test_logs() {
    LOGDIR="$WORKSPACE/unittests-logs/"
    BUILDROOT="$CONTRAIL_SOURCES/build"
    cd "$BUILDROOT"
    find . -name '*.log' | xargs gzip -S .txt.gz
    mkdir "$LOGDIR"
    find . -name '*.txt.gz' -exec cp --parents '{}' "$LOGDIR" \;
    chmod -R ugo+rX "$LOGDIR"
}

function display_test_results() {
    log="$1"
    fail_log=$WORKSPACE/$(basename "$log" .log)-FAIL.log

    echo "*****************************************************************"
    echo "Displaying test results from: $log"

    grep -Ew 'FAIL|TIMEOUT' $log|grep -v 'FAIL:' > $fail_log
    FAIL_COUNT=$(cat $fail_log | wc -l)
    PASS_COUNT=$(grep -w PASS $log | wc -l)

    echo
    echo "Number of PASS tests: $PASS_COUNT"
    echo "Number of FAIL tests: $FAIL_COUNT"

    if [[ $FAIL_COUNT -ne 0 ]]; then
        echo
        echo unit-test failures:
        echo
        cat $fail_log
    fi
    echo "*****************************************************************"
}

function analyze_test_results() {
    log=$1

    echo "Analyzing test results in: $log"
    FAIL_COUNT=$(grep -Ew 'FAIL|TIMEOUT' $log | grep -v 'FAIL:' | wc -l)

    if [[ $FAIL_COUNT -ne 0 ]]; then
        echo unit-test failures: $FAIL_COUNT
        exit_status=1
    fi
}

function determine_retry_list() {
    f="$1"
    retry_list=$WORKSPACE/retry_tests.txt

    grep --color=no -Ew 'FAIL|TIMEOUT' $f \
    | grep -v 'FAIL:' \
    | sed -e 's=^ *\([^ ]*\) *\(FAIL\|TIMEOUT\).*$=\1=' \
    | sed -r  's/\x1b\[[0-9;]*m?//g' > $retry_list

    echo "Analyzing list of failed unit-tests:"
    echo "================================================================"
    cat $retry_list
    echo "================================================================"

    retry_targets=$WORKSPACE/retry_targets.txt
    touch $retry_targets
    while read tc; do
        # Easy case is a failed C++ unit-test, so add it as target and carry on
        if [[ -r $tc ]]; then
            echo $tc | sed -e "s=\($CONTRAIL_SOURCES/.*\)=\1.log=" >> $retry_targets
            continue
        fi

        # Slightly harder, likely a python test and we have to find
        # the target that will rerun it
        bare_name=$(echo $tc | sed -e 's=[^_a-zA-Z0-9/]==g')

        py_file=$(find controller -name ${bare_name}.py -print)
        if [[ -n $py_file ]]; then
            py_file_count=$(echo $py_file | wc --words)
            if [[ $py_file_count -eq 1 ]]; then
            py_file_dir=$(dirname $py_file)
            bn=$(basename $py_file_dir)
            if [[ $bn =~ test ]]; then
                echo $(dirname $py_file_dir):test >> $retry_targets
                continue
            fi
            echo "Warn: $py_file does not appear to be in a test/tests dir"
            else
            echo "Warn: $py_file is not unique, cannot map to test target"
            fi
            echo "Warn: Cannot determine scons target to re-run failed test $tc"
            # rm -f $retry_list $retry_targets
            return 1
        fi

        # Let's see what repo grep shows us
        py_file=$(pytest_to_file $bare_name)
        if [[ -n $py_file ]]; then
            py_file_count=$(echo $py_file | wc --words)
            if [[ $py_file_count -ge 1 ]]; then
            py_file_dir=$(dirname $py_file | sort -u)
            bn=$(basename $py_file_dir)
            if [[ $bn =~ test ]]; then
                echo py_file_dir=$py_file_dir
                echo $(dirname $py_file_dir):test >> $retry_targets
                continue
            fi
            echo "Warn: $py_file does not appear to be in a test/tests dir"
            else
            echo "Warn: $py_file is not unique, cannot map to test target"
            fi
            echo "Warn: Cannot determine scons target to re-run failed test $tc"
            # rm -f $retry_list $retry_targets
            return 1
        fi

        echo "Warn: Cannot determine scons target to re-run failed test $tc"
        # rm -f $retry_list $retry_targets
        return 1
        done < $retry_list

        UNIT_TESTS=$(sort -u < $retry_targets)
        # rm -f $retry_list $retry_targets

        # Final sanity check... if UNIT_TESTS is empty, we have definitely
        # failed to determine retry tests
        if [[ -z $UNIT_TESTS ]]; then
            echo "Warn: cannot determine list of unit-tests to retry"
            return 1
        fi
    return 0
}

# Run unittests
function run_unittest() {
    _EXTRA_UNITTESTS=$(set +o | grep xtrace)
    set +o xtrace

    # Goto the repo top directory.
    cd $CONTRAIL_SOURCES

    export TASK_UTIL_WAIT_TIME=10000 # usecs
    export TASK_UTIL_RETRY_COUNT=6000
    export CONTRAIL_UT_TEST_TIMEOUT=1500
    export NO_HEAPCHECK=TRUE
    # This results in no -g flag during UT build, avoiding
    # disk-full failures for UT jobs.
    export CONTRAIL_COMPILE_WITHOUT_SYMBOLS=yes

    # Create CONTRAIL_REPO shortcut.
    export CONTRAIL_REPO="$WORKSPACE/contrail_repo"
    rm -rf "$CONTRAIL_REPO"
    ln -sf "$CONTRAIL_SOURCES" "$CONTRAIL_REPO"

    # Remove pip cache
    export PIP_CACHE=$HOME/.cache/pip
    [ -d $PIP_CACHE ] && rm -rf $PIP_CACHE

    # Find and run relevant tests.
    UNIT_TESTS=$($WORKSPACE/contrail-unittests-gather.rb)
    exit_code=$?
    if [ "$exit_code" != "0" ]; then
        echo "ERROR: Cannot determine unit-tests to run, exiting"
        ci_exit $exit_code
    fi

    if [[ -z $UNIT_TESTS ]]; then
        UNIT_TESTS=test
    fi

    logfile=$WORKSPACE/scons_test.log
    echo scons --debug=explain -k -j $SCONS_JOBS $UNIT_TESTS
    scons -k --debug=explain -j $SCONS_JOBS $UNIT_TESTS | tee $logfile
    exit_status=$?
    analyze_test_results $logfile
    # If unit test pass, show the results and exit    
    if [[ $exit_status -eq 0 ]]; then
        display_test_results $logfile
	ci_exit 0
    fi
    # if we didn't pass, try to get the list of failed tests
    echo "Unit-tests failed"
    determine_retry_list $logfile
    echo "info: displaying FAIL unit-test results"
    display_test_results $logfile
    ci_exit $exit_status
}

function main() {
    run_unittest
    ci_exit
}

# Note down environment
[ ! -f $WORKSPACE/env.sh ] && env > $WORKSPACE/env.sh
main
