#!/net/usr/local/bin/python

import jinja2 as ji
import validation_funs as vf
import os, subprocess, sys

TEMPLATE_DIR = "/projectnb/trenders/modules/packages/scene_processing/templates"
THISDIR = os.path.dirname(os.path.abspath(__file__))
TOPDIR = os.path.dirname(os.path.dirname(THISDIR))

def main(modelregion, outputfile):

	script = "cd " + THISDIR +"\n python stackagents.py " + modelregion.lower() + " " + outputfile

	param_dict = {'slots': "1", 
				  'run_time': "24:00:00", 
				  'job_name': "stck" + modelregion.lower(), 
				  'error_dir': os.path.join(TOPDIR, "log"),
				  'script': script}
	fname = os.path.join(TOPDIR, "log", "stackagents_" + modelregion.lower() + ".sh")

	enviro = ji.Environment(loader = ji.FileSystemLoader(TEMPLATE_DIR)) #set enviroment for templates
	template = enviro.get_template("qsub.sh")
	context = template.render(param_dict)
	f = open(fname, 'w')
	os.chmod(fname, 0755)
	f.write(context)
	f.close()

	subprocess.call('qsub ' + fname, shell=True)


if __name__ == '__main__': 
	args = sys.argv
	sys.exit(main(args[1], args[2]))