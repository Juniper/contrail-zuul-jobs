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
cmd = %{git ls-remote origin 2>/dev/null | \grep #{change_set} | \grep refs | awk '{print $1}'}

@dirs = { }
`#{cmd}`.split.each { |cid|
    next if cmd.to_s.empty?
    STDERR.puts "contrail-unittest-gather.rb: Parse SHA #{cid}\n"
    get_file = %{git show --pretty="format:" --name-only #{cid}}
    `#{get_file}`.split.each { |file|
        next if file.to_s.empty?
        STDERR.puts "contrail-unittest-gather.rb: Files parsed:\n #{file}\n"
        next if "#{project}/#{file}" !~ /(.*?\/.*?\/.*?)\//
        @dirs[$1] = true
    }
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
@all_tests = [ ]
json.each_pair { |module_name, module_data|
    @all_tests += module_data["scons_test_targets"]
    if module_data.key?("misc_test_targets")
        module_data["misc_test_targets"].each { |m|
            @all_tests += json[m]["scons_test_targets"]
        }
    end

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
    if module_data.key?("misc_test_targets")
        module_data["misc_test_targets"].each { |m|
            @tests += json[m]["scons_test_targets"]
        }
    end
}

# couldn't find changes in any specific project, so
# try to find default section and run generic test target
if @tests.empty?
    if json.key?('default')
        @tests += json['default']['scons_test_targets']
        json['default']['misc_test_targets'].each { |m|
            @tests += json[m]['scons_test_targets']
        }
    else
        @tests = @all_tests
    end
end

STDERR.puts "contrail-unittest-gather.rb: SCons targets to run:\n"
@tests.sort.uniq.each { |target|
    STDERR.puts "contrail-unittest-gather.rb:\t#{target}\n"
}

puts @tests.sort.uniq.join(" ") unless @tests.empty?
