import itertools
import os
import shlex
import subprocess
import sys
if len(sys.argv) <= 2:
  print "Please provide at least a execution and a library to execute"
  exit(1)

def getdep(pkg):
  """ Gets a list of dependencies from a given package"""
  cmd = 'apt-get -y build-dep -d %s' % pkg
  output = os.popen((cmd)).readlines()
  deplines = [line.rstrip('\n') for line in output if line.startswith("  ")]
  return shlex.split(deplines[0])

def getdep2(pkg):
  cmd = "apt-cache depends %s|grep Depends|cut -d':' -f2|grep -v '<'|sort|uniq" % pkg
  output = os.popen((cmd)).readlines()
  deplines = [line.rstrip('\n') for line in output]
  deplines = [line.lstrip(' ') for line in deplines]
  # verify if they are already installed (system libraries we dont want to copy)
  non_installed = []
  for dep in deplines:
    output = os.popen("dpkg -l %s" % dep).readlines()
    if len(output) == 0 or not output[-1].startswith("ii"):
      # This is not installed locally, lets see if we have already added it
      non_installed.append(dep)
  return non_installed

def getfiles(deps):
  """ Gets a list of files given a list of deps"""
  items = []
  # Actually download the deps
  for dep in deps:
    print "downloading dep %s" % dep
    os.popen("aptitude download %s" % dep)
    output = os.popen("ls").readlines()
    for line in output:
      if line.startswith("%s_" % dep):
        filename = line.rstrip('\n')
        os.popen("mv %s /var/cache/apt/archives" % filename)
    output = os.popen("find /var/cache/apt/archives/ -name '%s_*'" % dep).readlines()
    output = [line.rstrip('\n') for line in output]
    # Output is assumed to be a single library
    if len(output) > 1:
      raise "Too many output args"
    elif len(output) == 0:
      print "Couldnt find the arg that was downloaded %s" % dep
    items.append(output[0])
  return items

items = []
def recursive_getdeps(topdep):
  #print "getting deps for %s" % topdep
  items.append(topdep)
  deps = getdep2(topdep)
  #print deps
  for dep in deps:
    try: 
      # Check to see if the dep has been processed. if so skip it
      print "processing %s" % dep
      items.index(dep)
    except:
      # if it fails to find the index, we should process it
      items.append(dep)
      new_items = recursive_getdeps(dep)
      for item in new_items:
        try:
          items.index(item)
        except:
          items.append(item)
  return items

def recursive_uniq(topdep):
  """ Uniq's the result of the recursive getdeps"""
  return uniq(recursive_getdeps(package))

def uniq(seq): 
  # Not order preserving 
  keys = {} 
  for e in seq: 
      keys[e] = 1 
  return keys.keys()

execution = sys.argv[1]
package = sys.argv[2]
output_folder = sys.argv[3]
debrepo = sys.argv[4]

if execution == 'getdep':
  uninstalled_deps = uniq(recursive_getdeps(package))
  print "got the deps, now finding the files for %s files" % len(uninstalled_deps)
  files = getfiles(uninstalled_deps)
  print "got the files, now copying them"
  os.popen("mkdir -p %s" % output_folder)
  for file in files:
    os.popen("cp %s %s" % (file, output_folder))
  pass
elif execution == 'installdep':
  # Assume they are all in a folder
  print os.popen("reprepro -Vb %s includedeb lucid %s/*" % (debrepo, output_folder)).readlines()
else:
  print "Could not find a execution, exiting"
  exit(1)

