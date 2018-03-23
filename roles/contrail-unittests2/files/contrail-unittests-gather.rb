#!/usr/bin/env ruby

require 'rubygems'
require 'json'

exit(0) if ENV["ZUUL_CHANGES"] !~ /refs\/changes\/([^^]*)$/
change_set = $1

STDERR.puts "contrail-unittest-gather.rb: Choosing tests to execute\n"
contrail_sources = "#{ENV["WORKSPACE"]}/contrail-#{ENV["UPSTREAM_VERSION"]}"

json_file = "#{contrail_sources}/controller/ci_unittests.json"
exit(0) unless File.file?(json_file)

project = "controller"
project = "tools/sandesh" if ENV["ZUUL_PROJECT"] =~ /contrail-sandesh/
project = "tools/generateds" if ENV["ZUUL_PROJECT"] =~ /contrail-generateDS/
project = "vrouter" if ENV["ZUUL_PROJECT"] =~ /contrail-vrouter/
project = "src/contrail-common" if ENV["ZUUL_PROJECT"] =~ /contrail-common/
project = "src/contrail-analytics" if ENV["ZUUL_PROJECT"] =~ /contrail-analytics/
project = "src/contrail-api-client" if ENV["ZUUL_PROJECT"] =~ /contrail-api-client/

STDERR.puts "contrail-unittest-gather.rb: Review for project #{ENV["ZUUL_PROJECT"]}\n"
STDERR.puts "contrail-unittest-gather.rb: Check for commits for #{project}\n"

Dir.chdir("#{contrail_sources}/#{project}")

# Get the files changes in this change-set.
cmd = %{git ls-remote origin 2>/dev/null | \grep #{change_set} | \grep refs | awk '{print $1}' | xargs git show --pretty="format:" --name-only}

@dirs = { }
`#{cmd}`.split.each { |file|
    next if "#{project}/#{file}" !~ /(.*?\/.*?\/.*?)\//
    @dirs[$1] = true
}
STDERR.puts "contrail-unittest-gather.rb: List of directories changed:\n"
@dirs.each_key { |dir|
    STDERR.puts "contrail-unittest-gather.rb:\t#{dir}\n"
}

# Always test for changes to generateds and vrouter projects.
@dirs["tools/generateds"] = true if project == "tools/generateds"
@dirs["vrouter"] = true if project == "vrouter"

# Load unit-tests configuration
json = JSON.parse(File.read(json_file))

# Find all applicable scons test targets
@tests = [ ]
json.each_pair { |module_name, module_data|
    skip = true
    @dirs.each_key { |dir|
        if module_data["source_directories"].include?(dir) then
            # We need to run associated tests as the path matches.
            skip = false
            break
        end
    }
    next if skip

    @tests += module_data["scons_test_targets"]
    module_data["misc_test_targets"].each { |m|
        @tests += json[m]["scons_test_targets"]
    }
}

STDERR.puts "contrail-unittest-gather.rb: SCons targets to run:\n"
@tests.sort.uniq.each { |target|
    STDERR.puts "contrail-unittest-gather.rb:\t#{target}\n"
}

puts @tests.sort.uniq.join(" ") unless @tests.empty?
