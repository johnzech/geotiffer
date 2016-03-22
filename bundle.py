import os
import subprocess
import zipfile
import shutil

def zipdir(dir, zip):
    for dirname, subdirs, files in os.walk(dir):
        zip.write(dirname)
        for filename in files:
            zip.write(os.path.join(dirname, filename))

if __name__ == "__main__":
	if os.path.isdir('build'):
		shutil.rmtree('build')
	if os.path.isdir('geotiffer'):
		shutil.rmtree('geotiffer')
	if os.path.isdir('dist'):
		shutil.rmtree('dist')
	subprocess.call(['python', 'setup.py', 'py2exe'])
	os.rename('dist', 'geotiffer')
	shutil.copy('./redist/gdalwarp.exe', 'geotiffer')
	shutil.copy('./geotiffer.cfg', 'geotiffer')
	zipf = zipfile.ZipFile('geotiffer.zip', 'w')
	zipdir('geotiffer', zipf)
	shutil.rmtree('build')
	shutil.rmtree('geotiffer')

