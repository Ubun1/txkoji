import os
import re
import subprocess
import sys
from setuptools.command.test import test as TestCommand
from setuptools import setup, Command

readme = os.path.join(os.path.dirname(__file__), 'README.rst')
LONG_DESCRIPTION = open(readme).read()


def read_module_contents():
    with open('txkoji/__init__.py') as txkoji_init:
        return txkoji_init.read()


module_file = read_module_contents()
metadata = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", module_file))
version = metadata['version']


class BumpCommand(Command):
    """ Bump the __version__ number and commit all changes. """

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        version = metadata['version'].split('.')
        version[-1] = str(int(version[-1]) + 1)  # Bump the final part

        try:
            print('old version: %s  new version: %s' %
                  (metadata['version'], '.'.join(version)))
            raw_input('Press enter to confirm, or ctrl-c to exit >')
        except KeyboardInterrupt:
            raise SystemExit("\nNot proceeding")

        old = "__version__ = '%s'" % metadata['version']
        new = "__version__ = '%s'" % '.'.join(version)

        module_file = read_module_contents()
        with open('txkoji/__init__.py', 'w') as fileh:
            fileh.write(module_file.replace(old, new))

        # Commit everything with a standard commit message
        cmd = ['git', 'commit', '-a', '-m',
               'version %s' % '.'.join(version)]
        print(' '.join(cmd))
        subprocess.check_call(cmd)


class ReleaseCommand(Command):
    """ Tag and push a new release. """

    user_options = [('sign', 's', 'GPG-sign the Git tag and release files')]

    def initialize_options(self):
        self.sign = False

    def finalize_options(self):
        pass

    def run(self):
        # Create Git tag
        tag_name = 'v%s' % version
        cmd = ['git', 'tag', '-a', tag_name, '-m', 'version %s' % version]
        if self.sign:
            cmd.append('-s')
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Push Git tag to origin remote
        cmd = ['git', 'push', 'origin', tag_name]
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Push master branch to origin remote
        cmd = ['git', 'push', 'origin', 'master']
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Create source package
        cmd = ['python', 'setup.py', 'sdist']
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        tarball = 'dist/%s-%s.tar.gz' % ('txkoji', version)

        # GPG sign
        if self.sign:
            cmd = ['gpg2', '-b', '-a', tarball]
            print(' '.join(cmd))
            subprocess.check_call(cmd)

        # Upload
        cmd = ['twine', 'upload', tarball]
        if self.sign:
            cmd.append(tarball + '.asc')
        print(' '.join(cmd))
        subprocess.check_call(cmd)


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main('txkoji --flake8 ' +
                            self.pytest_args)
        sys.exit(errno)


setup(
    name='txkoji',
    description='Twisted API for Koji',
    packages=['txkoji'],
    author='Ken Dreyer',
    author_email='ktdreyer@ktdreyer.com',
    url='https://github.com/ktdreyer/txkoji',
    version=metadata['version'],
    license='MIT',
    zip_safe=False,
    keywords='koji, twisted',
    long_description=LONG_DESCRIPTION,
    classifiers=[
                 'Development Status :: 5 - Production/Stable',
                 'Framework :: Twisted',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'munch',
        'pyOpenSSL',  # for Kojis that use HTTPS
        'service_identity',  # for Kojis that use HTTPS
        'pyasn1',  # for Kojis that use HTTPS
        'twisted',
    ],
    tests_require=[
        'pytest-flake8',
        'pytest-twisted',
    ],
    cmdclass={'test': PyTest, 'bump': BumpCommand, 'release': ReleaseCommand},
)
