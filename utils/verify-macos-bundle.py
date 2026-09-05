import pathlib, subprocess, sys
app=pathlib.Path(sys.argv[1]); arch=sys.argv[2]
for file in app.rglob('*'):
 if not file.is_file() or file.is_symlink(): continue
 if 'Mach-O' not in subprocess.check_output(['file',str(file)],text=True): continue
 subprocess.run(['lipo','-verify_arch',arch,str(file)],check=True)
 for line in subprocess.check_output(['otool','-L',str(file)],text=True).splitlines()[1:]:
  dep=line.strip().split(' (')[0]
  if dep.startswith('/') and not dep.startswith(('/usr/lib/','/System/Library/')):
   raise SystemExit(f'External runtime dependency: {file}: {dep}')
print('Verified bundle architecture and dependency paths')
