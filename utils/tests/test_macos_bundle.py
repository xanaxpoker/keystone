"""Integration checks using small real Mach-O binaries, never vault contents."""
import importlib.util
import pathlib
import subprocess
import tempfile
import unittest

VERIFIER = pathlib.Path(__file__).resolve().parents[1] / 'verify-macos-bundle.py'
spec = importlib.util.spec_from_file_location('bundle', VERIFIER)
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.app = self.root / 'Fixture.app'
        self.bin = self.app / 'Contents/MacOS/Keystone'
        self.lib = self.app / 'Contents/Frameworks/libfixture.dylib'
        self.bin.parent.mkdir(parents=True)
        self.lib.parent.mkdir(parents=True)
        (self.root / 'main.c').write_text('int main(void) { return 0; }')
        (self.root / 'lib.c').write_text('int fixture(void) { return 0; }')
        (self.root / 'link.c').write_text('extern int fixture(void); int main(void) { return fixture(); }')
        self.compile('arm64')

    def run_command(self, *args):
        subprocess.run(args, check=True, capture_output=True)

    def compile(self, arch):
        self.run_command('clang', '-arch', arch, str(self.root / 'main.c'), '-o', str(self.bin))

    def with_library(self, install_name='@rpath/libfixture.dylib'):
        self.run_command('clang', '-arch', 'arm64', '-dynamiclib', str(self.root / 'lib.c'),
                         '-Wl,-install_name,' + install_name, '-o', str(self.lib))
        self.run_command('clang', '-arch', 'arm64', str(self.root / 'link.c'),
                         '-L' + str(self.lib.parent), '-lfixture',
                         '-Wl,-rpath,@executable_path/../Frameworks', '-o', str(self.bin))

    def test_arm64(self):
        bundle.verify(self.app, 'arm64')

    def test_intel(self):
        self.compile('x86_64')
        bundle.verify(self.app, 'x86_64')

    def test_wrong_architecture(self):
        with self.assertRaises(subprocess.CalledProcessError):
            bundle.verify(self.app, 'x86_64')

    def test_bundled_library(self):
        self.with_library()
        bundle.verify(self.app, 'arm64')

    def test_plugin_install_id_is_not_a_dependency(self):
        plugin = self.app / 'Contents/PlugIns/platforms/libplugin.dylib'
        plugin.parent.mkdir(parents=True)
        self.run_command('clang', '-arch', 'arm64', '-dynamiclib', str(self.root / 'lib.c'),
                         '-Wl,-install_name,@rpath/libplugin.dylib', '-o', str(plugin))
        bundle.verify(self.app, 'arm64')

    def test_missing_library(self):
        self.with_library()
        self.lib.unlink()
        with self.assertRaisesRegex(ValueError, 'Unresolved or external'):
            bundle.verify(self.app, 'arm64')

    def test_external_library(self):
        self.with_library(str(self.lib))
        with self.assertRaisesRegex(ValueError, 'External runtime dependency'):
            bundle.verify(self.app, 'arm64')

    def test_library_symlink_escaping_bundle(self):
        self.with_library()
        external = self.root / 'external.dylib'
        self.lib.rename(external)
        self.lib.symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'Unresolved or external'):
            bundle.verify(self.app, 'arm64')


if __name__ == '__main__':
    unittest.main()
