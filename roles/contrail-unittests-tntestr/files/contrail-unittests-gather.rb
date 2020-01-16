#!/usr/bin/env ruby

require 'rubygems'
require 'json'

STDERR.puts "contrail-unittest-gather.rb: ZUUL_CHANGES=#{ENV["ZUUL_CHANGES"]}\n"

if ENV["ZUUL_CHANGES"] !~ /refs\/changes\/([^^]*)$/ then
    STDERR.puts "contrail-unittest-gather.rb: ignoring because of invalid ZUUL_CHANGES env variable\n"
    exit(0)
end

contrail_sources = "#{ENV["WORKSPACE"]}/contrail-#{ENV["UPSTREAM_VERSION"]}"

json_file = "#{contrail_sources}/controller/ci_unittests.json"
unless File.file?(json_file) then
    STDERR.puts "contrail-unittest-gather.rb: ignoring because file not found: #{json_file}\n"
    exit(0)
end

# Load unit-tests configuration
json = JSON.parse(File.read(json_file))

STDERR.puts "contrail-unittest-gather.rb: Choosing tests to execute\n"

@tests = [ ]
@all_tests = [ ]

ENV["ZUUL_CHANGES"].split(',').each { |zc|
    zc =~ /(.*)\^refs\/changes\/(.*)$/
    project = $1
    patchset = $2

    STDERR.puts "contrail-unittest-gather.rb: Patchset #{patchset} for repo #{project}\n"

    project = "controller" if project =~ /contrail-controller$/
    project = "tools/sandesh" if project =~ /contrail-sandesh$/
    project = "tools/generateds" if project =~ /contrail-generateDS$/
    project = "vrouter" if project =~ /contrail-vrouter$/
    project = "src/contrail-common" if project =~ /contrail-common$/
    project = "src/contrail-analytics" if project =~ /contrail-analytics$/
    project = "src/contrail-api-client" if project =~ /contrail-api-client$/
    project = "vcenter-manager" if project =~ /contrail-vcenter-manager$/
    project = "vcenter-fabric-manager" if project =~ /contrail-vcenter-fabric-manager$/

    next unless File.directory?("#{contrail_sources}/#{project}")
    STDERR.puts "contrail-unittest-gather.rb: Repo is in local directory #{project}\n"
    Dir.chdir("#{contrail_sources}/#{project}")

    @dirs = { }
    cmd = %{git ls-remote origin 2>/dev/null}
    `#{cmd}`.split('\n').each { |l|
        next if l !~ /^\s*(\S+)\s.*refs.*#{patchset}/
	cid = $1
        STDERR.puts "contrail-unittest-gather.rb: Found commit #{cid}\n"
        get_file = %{git show --pretty="format:" --name-only "#{cid}"}
        `#{get_file}`.split.each { |file|
            next if file.to_s.empty?
            STDERR.puts "contrail-unittest-gather.rb: Found committed file:\n #{file}\n"
            next if "#{project}/#{file}" !~ /(.*)\//
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

    # Find all applicable scons test targets
    json.each_pair { |module_name, module_data|
        @all_tests += module_data["scons_test_targets"]
        if module_data.key?("misc_test_targets")
            module_data["misc_test_targets"].each { |m|
                @all_tests += json[m]["scons_test_targets"]
            }
        end

        @want_dirs = module_data["source_directories"]
        skip = true
        @dirs.each_key { |dir|
            next if @want_dirs.nil?
            @want_dirs.each { |want_dir|
                if "#{dir}/" =~ /^#{want_dir}\// then
                    # We need to run associated tests as the path matches.
                    STDERR.puts "contrail-unittest-gather.rb: path #{dir} matches #{want_dir} specified for #{module_name}\n"
                    skip = false
                    break
                end
            }
        }
        next if skip

        @tests += module_data["scons_test_targets"]
        if module_data.key?("misc_test_targets")
            module_data["misc_test_targets"].each { |m|
                @tests += json[m]["scons_test_targets"]
            }
        end
    }
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
