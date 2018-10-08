#!/usr/bin/env python

from argparse import ArgumentParser
import glob
import re
import subprocess
import commands as cmd
import ROOT
from XRootD import client
from XRootD.client.flags import DirListFlags, OpenFlags, MkDirFlags, QueryCode

def check_root_ok(filename, treename="Delphes"):
    retval=True
    #rfile = ROOT.TFile(filename,"READ")
    rfile = ROOT.TFile.Open(filename)
    if rfile.TestBit(ROOT.TFile.kRecovered) : retval = False
    if rfile.IsZombie(): 
        rfile.Close()
        return False
    tree = rfile.Get(treename)
    if (not tree) or tree.IsZombie(): retval = False
    rfile.Close()
    return retval

def submitToBatch(JobId):
    batch_command = 'bsub -f "/tmp/x509up_u13125 > /tmp/x509up_u13125" -q 1nh {0}'.format(JobId)
    print batch_command
    output = subprocess.Popen(batch_command, stdout=subprocess.PIPE,
                              shell=True).communicate()[0]
    match = re.match('Job <(\d*)> is', output)
    #jobID = match.group(1)
    #return jobID


parser = ArgumentParser('validate delphes root files in a directory')
#parser.add_argument('directory')
parser.add_argument('--SER')
parser.add_argument('--DIR')
args = parser.parse_args()

myclient = client.FileSystem(args.SER+':1094')
status, listing = myclient.dirlist(args.DIR, DirListFlags.STAT)
print listing.parent

rootfiles = []
onlyrootfilenames = []
for entry in listing:
    rootfiles.append(args.SER+'/'+args.DIR+entry.name)
    onlyrootfilenames.append(entry.name)
#rootfiles = glob.glob(args.directory+"/*.root")
brokenfiles=[]
allfiles=len(rootfiles)
counter=0
for file in rootfiles:
    #if counter>1: continue
    print('Submitting '+file+'... '+str(int(float(counter)/float(allfiles)*1000)/10.)+'%')
    counter+=1
    if not True: #check_root_ok(file):
        print('broken: '+file)
    else:
        INDEX=rootfiles.index(file)
        FILENAME=onlyrootfilenames[INDEX].split(".")[0]
        PATHTOREMOTEDIR=args.SER+'/'+args.DIR
        cmd.getoutput("cp config/TemplateConfig.txt config/TemplateConfig_{0}_.txt".format(FILENAME))
        cmd.getoutput("cp JobTemplate.sh JobTemplate_{0}_.sh".format(FILENAME))
        cmd.getoutput("sed -i -- 's#REMOTEDIRECTORY#{0}#g' config/TemplateConfig_{1}_.txt".format(PATHTOREMOTEDIR,FILENAME))
        cmd.getoutput("sed -i -- 's/FILETORUNOVER/{0}/g' config/TemplateConfig_{1}_.txt".format(onlyrootfilenames[INDEX],FILENAME))
        cmd.getoutput("sed -i -- 's/PROCESSNAME/{0}/g' config/TemplateConfig_{1}_.txt".format(FILENAME,FILENAME))
        cmd.getoutput("sed -i -- 's/JOBCONFIGTORUN/TemplateConfig_{0}_.txt/g' JobTemplate_{1}_.sh".format(FILENAME,FILENAME))
        submitToBatch("JobTemplate_{0}_.sh".format(FILENAME))
