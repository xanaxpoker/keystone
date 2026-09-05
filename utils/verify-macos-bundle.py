"""Reject wrong-architecture binaries and nonportable macOS bundle dependencies."""
import pathlib
import subprocess
import sys


def output(*args):
    return subprocess.check_output(args, text=True)


def verify(app, arch):
    app = pathlib.Path(app).resolve()
    executable_dir = app / 'Contents/MacOS'
    main = executable_dir / 'Keystone'
    if not main.is_file():
        raise ValueError(f'Missing executable: {main}')

    def expand(path, binary):
        return pathlib.Path(path.replace('@loader_path', str(binary.parent))
                            .replace('@executable_path', str(executable_dir)))

    def rpaths(binary):
        lines = output('otool', '-l', str(binary)).splitlines()
        result = []
        for i, line in enumerate(lines):
            if line.strip() == 'cmd LC_RPATH':
                value = lines[i + 2].strip().removeprefix('path ').split(' (offset ')[0]
                result.append(expand(value, binary))
        return result

    main_paths = rpaths(main)
    count = 0
    for binary in app.rglob('*'):
        if not binary.is_file() or binary.is_symlink():
            continue
        if 'Mach-O' not in output('file', str(binary)):
            continue
        count += 1
        subprocess.run(['lipo', str(binary), '-verify_arch', arch], check=True)
        search_paths = rpaths(binary) + main_paths
        install_ids = output('otool', '-D', str(binary)).splitlines()[1:]
        for position, line in enumerate(output('otool', '-L', str(binary)).splitlines()[1:]):
            dependency = line.strip().split(' (')[0]
            # otool -L lists a dylib's LC_ID_DYLIB first; it is its identity,
            # not a load dependency (plugins need not resolve their own ID).
            if position == 0 and dependency in install_ids:
                continue
            if dependency.startswith(('/usr/lib/', '/System/Library/')):
                continue
            if dependency.startswith('@rpath/'):
                relative = dependency.removeprefix('@rpath/')
                candidates = [directory / relative for directory in search_paths]
            elif dependency.startswith(('@loader_path/', '@executable_path/')):
                candidates = [expand(dependency, binary)]
            else:
                raise ValueError(f'External runtime dependency: {binary}: {dependency}')
            resolved = [p.resolve() for p in candidates if p.is_file()]
            if not any(app in p.parents for p in resolved):
                raise ValueError(f'Unresolved or external runtime dependency: {binary}: {dependency}')
    print(f'Verified {count} Mach-O files for {arch}; all non-system dependencies resolve inside the bundle')


if __name__ == '__main__':
    verify(sys.argv[1], sys.argv[2])
