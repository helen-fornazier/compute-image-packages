#!/usr/bin/python
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Create a Python package of the Linux guest environment."""

import glob

import fnmatch
import os
import platform
import setuptools
import setuptools.command.build_py

class ReplaceVarsCommand(setuptools.command.build_py.build_py):
    """Custom command to replace variables inside the code according with the current system """

    def findReplace(self, directory, find, replace, filePattern):
        for path, dirs, files in os.walk(os.path.abspath(directory)):
            for filename in fnmatch.filter(files, filePattern):
                filepath = os.path.join(path, filename)
                with open(filepath) as f:
                    s = f.read()
                s = s.replace(find, replace)
                with open(filepath, "w") as f:
                    f.write(s)

    def run(self):
        replace = {}
        if platform.system == "FreeBSD":
            replace["%%LOCALBASE%%"] = "/usr/local"
            replace["%%BOTOCFG%%"] = "/usr/local"
            replace["%%CFGDIR%%"] = "/usr/local/etc"
            replace["%%VARLOCK%%"] = "/var/spool/lock"

        elif platform.system == "OpenBSD":
            replace["%%LOCALBASE%%"] = "/usr/local"
            replace["%%BOTOCFG%%"] = ""
            replace["%%CFGDIR%%"] = "/usr/local/etc"
            replace["%%VARLOCK%%"] = "/var/spool/lock"

        else:
            replace["%%LOCALBASE%%"] = ""
            replace["%%BOTOCFG%%"] = ""
            replace["%%CFGDIR%%"] = "/etc/default"
            replace["%%VARLOCK%%"] = "/var/lock"

        for k in replace:
            self.findReplace("build", k, replace[k], "*.py")

class BuildPyCommand(setuptools.command.build_py.build_py):
    """Custom build command."""

    def run(self):
        setuptools.command.build_py.build_py.run(self)
        self.run_command('replace_vars')

setuptools.setup(
    author='Google Compute Engine Team',
    author_email='gc-team@google.com',
    description='Google Compute Engine',
    include_package_data=True,
    install_requires=['boto', 'setuptools'],
    license='Apache Software License',
    long_description='Google Compute Engine guest environment.',
    name='google-compute-engine',
    packages=setuptools.find_packages(),
    scripts=glob.glob('scripts/*'),
    url='https://github.com/GoogleCloudPlatform/compute-image-packages',
    version='2.4.0',
    cmdclass={
        'replace_vars': ReplaceVarsCommand,
        'build_py': BuildPyCommand,
    },
    # Entry points create scripts in /usr/bin that call a function.
    entry_points={
        'console_scripts': [
            'google_accounts_daemon=google_compute_engine.accounts.accounts_daemon:main',
            'google_clock_skew_daemon=google_compute_engine.clock_skew.clock_skew_daemon:main',
            'google_ip_forwarding_daemon=google_compute_engine.ip_forwarding.ip_forwarding_daemon:main',
            'google_instance_setup=google_compute_engine.instance_setup.instance_setup:main',
            'google_network_setup=google_compute_engine.network_setup.network_setup:main',
            'google_metadata_script_runner=google_compute_engine.metadata_scripts.script_manager:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
    ],
)
