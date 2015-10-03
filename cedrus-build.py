#!/usr/bin/env python

import os, subprocess, time, sys, glob, shutil, datetime, platform


qt_binary_location = os.getenv( 'QT_BINARIES_REPO', '' )

if qt_binary_location == '':
    print 'FAIL. must set the evn var $QT_BINARIES_REPO to your checkout of https://github.com/cedrus/qt-binaries'
    print 'PLEASE NOTE: checkout qt-binaries, then run "set_env.py" (part of qt-binaries). That will set QT_BINARIES_REPO.'
    exit()

if ( False == os.path.exists( qt_binary_location ) ) or ( False == os.path.isdir( qt_binary_location ) ):
    print 'FAIL. script cannot verify that "' + str( qt_binary_location ) + '" ($QT_BINARIES_REPO) is a directory'
    exit()

if ( os.path.exists( '/sw/lib' ) ) or ( os.path.isdir( '/sw/lib' ) ):
    print 'FAIL. you must temporarily hide (rename) your /sw/lib directory to build Qt. linking to libs in /sw will not work for customers'
    print '      (NOTE: it is simplest to hide the base [sw] dir, otherwise [/sw/bin] is there but [/sw/lib] is not, leading to issues.)'
    exit()

if ( os.path.exists( '/usr/local/Cellar' ) ) or ( os.path.isdir( '/usr/local/Cellar' ) ):
    print 'FAIL. you must temporarily hide (rename) your /usr/local/Cellar directory to build Qt. linking to libs in homebrew will not work for customers'
    exit()

if sys.platform == 'win32':
    test_01 = os.getenv( 'VCINSTALLDIR', '' )
    test_02 = os.getenv( 'LIBPATH', '' )
    test_03 = os.getenv( 'DEVENVDIR', '' )

    if test_01 == '' or test_02 == '' or test_03 == '':
        """
        It seems simplest to just require that the user open the Visual Studio cmd window.
        Otherwise, in past scripts we have put the following into a BAT file:
            @call "%VS100COMNTOOLS%\..\..\VC\vcvarsall.bat" x86
        """
        print 'FAIL. cannot run from default CMD prompt. use Visual Studio Command Prompt or execute vcvarsall.bat'
        exit()

def wait_for_process( p ):
    running_stuff = True
    while running_stuff:
        retcode = p.poll()
        if retcode is not None:
            running_stuff = False
            time.sleep(.05) # fraction of a second


# the next line DID NOT WORK! i ended up setting CXXFLAGS at the top of: qt/qtbase/configure
#os.environ[ 'QMAKE_CXXFLAGS' ] = '-std=c++11 -stdlib=libc++'

# the next line FAILED TO WORK. i ended up setting LDFLAGS at the top of: qt/qtbase/configure
#os.environ[ 'QMAKE_LFLAGS' ] = '-stdlib=libc++'

build_command_01 = './configure -prefix ' + qt_binary_location + '/macosx/ -platform macx-clang -no-framework'
build_command_02 = 'make -j6 module-qtquick1'                       # should also build qtbase, since qtquick depends on qtbase
build_command_03 = 'make -j6 module-qtquick1-install_subtargets'    # should also build qtbase, since qtquick depends on qtbase
build_command_04 = 'make -j6 module-qtquickcontrols'
build_command_05 = 'make -j6 module-qtquickcontrols-install_subtargets'

if sys.platform == 'win32':
    build_command_01 = str( 'configure.bat -platform win32-msvc2010 -no-cetest -prefix "' +
                            qt_binary_location + '\win32\"')
    build_command_02 = 'nmake module-qtquick1'                       # should also build qtbase, since qtquick depends on qtbase
    build_command_03 = 'nmake module-qtquick1-install_subtargets'    # should also build qtbase, since qtquick depends on qtbase
    build_command_04 = 'nmake module-qtquickcontrols'
    build_command_05 = 'nmake module-qtquickcontrols-install_subtargets'

p = subprocess.Popen(build_command_01, shell=True)
wait_for_process(p)

p = subprocess.Popen(build_command_02, shell=True)
wait_for_process(p)

p = subprocess.Popen(build_command_03, shell=True)
wait_for_process(p)

p = subprocess.Popen(build_command_04, shell=True)
wait_for_process(p)

p = subprocess.Popen(build_command_05, shell=True)
wait_for_process(p)

# where the main qt dylibs are:
# /Users/kkheller/Documents/qt5_bins/macosx/lib

# other ones found (RECURSIVELY) here:
# /Users/kkheller/Documents/qt5_bins/macosx/plugins


"""
If you want to WIPE CLEAN the whole destination area before building
new qt binaries, then as of Oct 2015 i can recommend the following:

cd ../qt-binaries/macosx/
rm -rf *   # clear out everything under /macosx/
mkdir final-lib  # you need to RESTORE THIS FOLDER. (but it can begin EMPTY)
git checkout cedrus_qt_mach-o_dylib_fixer.py  # you must restore this SINGLE script
"""

os_dir_name = 'macosx'
lib_suffixes = ['dylib']

if sys.platform == 'win32':
    os_dir_name = 'win32'
    lib_suffixes = ['dll','lib']

def copy_plugins_to_lib_dir( plugin_dir, lib_dir ):
    global lib_suffixes

    for root, sub_folders, files in os.walk( plugin_dir ):

        for f in files:
            source = os.path.join(root, f)
            not_symlink = (False == os.path.islink( str(source) ) )
            is_lib = False
            for suf in lib_suffixes:
                if f.endswith( suf ):
                    is_lib = True
                    break

            if not_symlink and is_lib:
                destination = os.path.join( lib_dir, f )
                print 'moving [' + str( source ) + '] over to [' + str(destination) + ']'
                shutil.copy2(source, destination)

what_to_walk = qt_binary_location + os.sep + os_dir_name + os.sep + 'plugins'
where_to_copy_to = qt_binary_location + os.sep + os_dir_name + os.sep + 'final-lib' + os.sep

copy_plugins_to_lib_dir( what_to_walk, where_to_copy_to )

what_to_walk = qt_binary_location + os.sep + os_dir_name + os.sep + 'imports'
copy_plugins_to_lib_dir( what_to_walk, where_to_copy_to )

what_to_walk = qt_binary_location + os.sep + os_dir_name + os.sep + 'qml'
copy_plugins_to_lib_dir( what_to_walk, where_to_copy_to )

what_to_walk = qt_binary_location + os.sep + os_dir_name + os.sep + 'lib'
copy_plugins_to_lib_dir( what_to_walk, where_to_copy_to )


if sys.platform == 'darwin':
    # now run install_name_tool to update all mac dylibs to @executable_path
    command_04 = str( qt_binary_location + os.sep
                      + 'macosx' + os.sep
                      + 'cedrus_qt_mach-o_dylib_fixer.py '
                      + where_to_copy_to )

    p = subprocess.Popen(command_04, shell=True)

    wait_for_process(p)

