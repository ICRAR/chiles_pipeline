"""
Make cubes based on serial version loop_cube.py and loop_split.py

This module should run together with the casapy: e.g. casapy --nologger -c makecube.py
"""

import os
import commands
import time
import os.path

INPUT_VIS_SUFFIX = '_calibrated_deepfield.ms'

def execCmd(cmd, failonerror = True, okErr = []):
    """
    Execute OS command from within Python
    """
    re = commands.getstatusoutput(cmd)
    if (re[0] != 0 and not (re[0] in okErr)):
        errMsg = 'Fail to execute command: "%s". Exception: %s' % (cmd, re[1])
        if (failonerror):
            raise Exception(errMsg)
        else:
            print errMsg
    return re

def getMyObs(job_id, obs_dir, obs_first, obs_last, num_jobs):
    """
    Return a list of Obs that this job has to split
    Since the num_jobs could be less than num_obs, a job may need to
    process more than one obs

    """
    ret = []
    lsre = execCmd('ls %s' % obs_dir)
    all_obs = lsre[1].split('\n')

    for i in xrange(obs_first + job_id, obs_last + 1, num_jobs):
        ret.append(all_obs[i])

    return ret, all_obs[obs_first:obs_last + 1]


def check_dir(this_dir, createOnMissing = True):
    """
    Return    True if the directory is there
    """
    if not os.path.exists(this_dir):
        if createOnMissing:
            cmd = 'mkdir -p %s' % this_dir
            execCmd(cmd)

            if not os.path.exists(this_dir):
                raise Exception('Fail to create directory %s' % this_dir)
            return True
        else:
            return False
    else:
        return True

def createCubeDoneMarker(casa_workdir, run_id, freq_range):
    return '%s/%s_cube_%s_done' % (casa_workdir, run_id, freq_range.replace('~', '-'))

def do_cube(in_dirs,cube_dir,min_freq,max_freq,step_freq, width_freq, job_id, num_jobs, debug):
    """
    adapted from loop_cube.py with
    (1) extra parameters for job management
    (2) remove the concatenation, move it outside
    (3) deal with (max_freq - min_freq) % width_freq > 0
    """

    if (sel_freq):
        steps = (max_freq - min_freq) / step_freq # a list of all frequency split
        rem = (max_freq - min_freq) % step_freq
        if (rem):
            steps += 1

        freq1 = min_freq + job_id * step_freq
        freq2 = freq1 + step_freq
    else:
        steps = 1
    cube_names = []
    for i in xrange(job_id, steps, num_jobs):
        if (sel_freq):
            if (rem and (i == steps - 1)):
                freq_range = '%d~%d' % (min_freq + i * step_freq, max_freq)
            else:
                freq_range = str(freq1) + '~' + str(freq2)
        else:
            freq_range = 'min~max'
        in_files = []
        outfile = cube_dir + 'cube_' + freq_range

        for j in range(len(in_dirs)):
            # check whether the file exists without issues ...
            workfile = in_dirs[j] + 'vis_' + freq_range
            if (not debug):
                print workfile
                print os.path.isdir(workfile)
                if os.path.isdir(workfile) == True:
                    # make a visfile with all the directories
                    in_files = in_files + [in_dirs[j] + 'vis_' + freq_range]
                else:
                    print 'WARNING, file is missing: ' + workfile
            else:
                in_files = in_files + [in_dirs[j] + 'vis_' + freq_range]


        #print 'working on: ' + outfile
        #print 'input visibilities:', in_files
        #print 'input visibilities:', in_files
        if (debug):
            print '\nJob %d: clean(vis=%s,\timagename=%s)' % (job_id, str(in_files), outfile)
        else:
            print '\nJob %d: clean(vis=%s,\timagename=%s)' % (job_id, str(in_files), outfile)
            try:
                clean(vis=in_files,
                      imagename=outfile,
                      field='deepfield',
                      spw='',
                      mode='frequency',
                      restfreq='1420.405752MHz',
                      nchan=-1,
                      start='',
                      width='',
                      interpolation='nearest',
                      niter=0,
                      gain=0.1,
                      threshold='0.0mJy',
                      imsize=[2048],
                      cell=['1.5arcsec'],
                      weighting='briggs',
                      robust=0.0,
                      usescratch=True)
            except Exception, clEx:
                print '*********\nClean exception: %s\n***********' % str(clEx)


        freq1 = freq1 + (num_jobs * step_freq)
        freq2 = freq2 + (num_jobs * step_freq)

        done_02_f = createCubeDoneMarker(casa_workdir, run_id, freq_range)
        if (debug):
            print 'Job %d: Creating done_02_f: %s' % (job_id, done_02_f)
        open(done_02_f, 'a').close() # create the file marking the completion of this freq range
    return

def combineAllCubes(cube_dir,outname,min_freq,max_freq,step_freq,casa_workdir,run_id, debug, timeout = 100):
    if (sel_freq):
        steps = (max_freq - min_freq) / step_freq
        rem = (max_freq - min_freq) % step_freq
        if (rem):
            steps += 1
    else:
        steps = 1

    cube_names = []

    missing_freqs = []
    done_freq = {}

    # first wait for all freq splits are "cleaned" into sub-cubes
    for j in range(timeout):
        freq1 = min_freq
        freq2 = min_freq + step_freq
        for i in range(steps):
            if (sel_freq):
                if (rem and (i == steps - 1)):
                    freq_range = '%d~%d' % (min_freq + i * step_freq, max_freq)
                else:
                    freq_range = str(freq1) + '~' + str(freq2)
            else:
                freq_range = 'min~max'
            if (not done_freq.has_key(freq_range)):
                done_02_f = createCubeDoneMarker(casa_workdir, run_id, freq_range)
                if (os.path.exists(done_02_f)):
                    done_freq[freq_range] = 1
            freq1 = freq1 + step_freq
            freq2 = freq2 + step_freq
        gap = steps - len(done_freq.keys())
        if (0 == gap):
            break
        else:
            if (j % 60 == 0): # report every one minute
                print 'Still need %d freq to be cubed' % gap
            time.sleep(1)

    gap = steps - len(done_freq.keys())
    if (gap > 0):
        print 'job %d timed out when waiting for concatenation, steps = %d, but done_freq = %d' % (job_id, steps, len(done_freq.keys()))
    else:
        print 'job %d found all sub-cubes are ready' % job_id

    # then loop through to form the cube name list for final concatenation
    freq1 = min_freq
    freq2 = min_freq + step_freq
    for i in range(steps):
        if (sel_freq):
            if (rem and (i == steps - 1)):
                freq_range = '%d~%d' % (min_freq + i * step_freq, max_freq)
            else:
                freq_range = str(freq1) + '~' + str(freq2)
        else:
            freq_range = 'min~max'

        in_files = []
        outfile = cube_dir + 'cube_' + freq_range

        freq1 = freq1 + step_freq
        freq2 = freq2 + step_freq

        subcube = outfile + '.image'
        if (not debug):
            if os.path.isdir(subcube) == True:
                #cube_names = np.append(cube_names,subcube)
                # cube_names = cube_names + [subcube]
                cube_names.append(subcube)
            else:
                print 'WARNING, subcube is missing : ' + subcube
        else:
            #cube_names = cube_names + [subcube]
            cube_names.append(subcube)

    if (debug):
        print '\nJob %d: Concatenating all cubes...\n\tia.imageconcat(infiles=%s,outfile=%s,relax=T)' % (job_id, str(cube_names), outname)
    else:
        print 'Start concatenating %s' % str(cube_names)
        final=ia.imageconcat(infiles=cube_names,outfile=outname,relax=T)
        final.done()

    return

def createSplitDoneMarker(casa_workdir, run_id, obsId):
    return '%s/%s__%s__split_done' % (casa_workdir, run_id, obsId)

def checkIfAllObsSplitDone(casa_workdir, job_id, run_id, all_obs, timeout = 100):
    """
    """
    print 'Waiting for all obs split to be completed....'
    done_obs = {} #
    for i in range(timeout):
        for obs in all_obs:
            infile_dir = '%s/%s' % (obs_dir, obs)
            obsId = os.path.basename(infile_dir).replace('_FINAL_PRODUCTS', '')
            if (done_obs.has_key(obsId)):
                continue
            done_01_f = createSplitDoneMarker(casa_workdir, run_id, obsId)
            if (os.path.exists(done_01_f)):
                done_obs[obsId] = 1
        gap = len(all_obs) - len(done_obs.keys())
        if (0 == gap):
            break
        else:
            if (i % 60 == 0): # report every one minute
                print 'Still need %d obs to be split' % gap
            time.sleep(1)

    gap = len(all_obs) - len(done_obs.keys())
    if (gap > 0):
        print 'job %d timed out when waiting for all obs to be split' % job_id
    else:
        print 'job %d found all obs have been split' % job_id
    return done_obs


# load all environment variables to set up configuration

def do_cvel(infile,outdir,backup_dir,min_freq,max_freq,step_freq,width_freq,spec_window, obsId):
    """
    Adapted from loop.split.py with changes
    (1) deal with (max_freq - min_freq) % step_freq > 0
    (2) some debug info
    (3) obsId parameter for marking split_done
    """

    if (not os.path.exists(outdir)):
        os.system('mkdir ' + outdir)
    if (not os.path.exists(backup_dir)):
        os.system('mkdir ' + backup_dir)

    steps = (max_freq - min_freq) / step_freq
    rem = (max_freq - min_freq) % step_freq
    if (rem):
        steps += 1
    freq1 = min_freq
    freq2 = min_freq + step_freq

    if (not sel_freq):
        steps = 1

    for i in range(steps):
        if (sel_freq):
            if (rem and (i == steps - 1)):
                freq_range = '%d~%d' % (min_freq + i * step_freq, max_freq)
            else:
                freq_range = str(freq1) + '~' + str(freq2)
            spw_range = spec_window + ':' + freq_range + 'MHz'
        else:
            freq_range = 'min~max'
            spw_range = spec_window


        spw_range = spec_window
        no_chan=int(step_freq*1000.0/width_freq)  # MHz/kHz!!
# I think I always want this with cvel.

        outfile = outdir + 'vis_' + freq_range
        backupfile = backup_dir + 'vis_' + freq_range
        if (not debug):
            os.system('rm -rf ' + outfile)
            os.system('rm -rf ' + backupfile)
            print 'working on: ' + outfile
            try:
                cvel(vis=infile,
                      outputvis=outfile,
                      restfreq='1420.405752MHz',
                      mode='frequency',
                      nchan=no_chan,
                      outframe='lsrk',
                      interpolation='linear',
                      veltype='radio',
                      start=str(freq1)+'MHz',
                      width=str(width_freq)+'kHz',
                      spw=spw_range)
            except Exception, spEx:
                print '*********\nSplit exception: %s\n***********' % str(spEx)
        else:
            msg = "\ncvel(vis=%s,\noutputvis=%s,\nstart=%s,width=%s,spw=%s,nchan=%d)"\
            % (infile, outfile, str(freq1)+'MHz', width_freq, spw_range,no_chan)
            print msg

        freq1 = freq1 + step_freq
        freq2 = freq2 + step_freq

        # as precaution make a backup copy of the split vis files
        # very often when casa crashes, the original file becomes corrupted ...

        if (not debug and bkp_split):
            os.system('cp -r ' + outfile + ' '  + backupfile)

    done_01_f = createSplitDoneMarker(casa_workdir, run_id, obsId)
    if (debug):
        print '\nJob %d: Creating done_01_f: %s' % (job_id, done_01_f)
    open(done_01_f, 'a').close() #create the file marking the completion of splitting of this obs
    return

debug = int(os.getenv('CH_MODE_DEBUG', '0'))
null_str = 'N/A'
null_int = '-1'
spec_window = os.getenv('CH_SPW', '*')
if ('ALL' == spec_window.upper()):
    spec_window = '*'
host_name = os.getenv('HOSTNAME', 'myhost')
job_id = int(os.getenv('PBS_ARRAYID', '-1'))
# e.g. 19625[0].pleiades.icrar.org --> 19625
run_id = os.getenv('CH_RUN_ID', null_str).split('[')[0]
obs_dir = os.getenv('CH_OBS_DIR', null_str)
obs_first = int(os.getenv('CH_OBS_FIRST', null_int))
obs_last = int(os.getenv('CH_OBS_LAST', null_int))
freq_min = int(os.getenv('CH_FREQ_MIN', null_int))
freq_max = int(os.getenv('CH_FREQ_MAX', null_int))
freq_width = float(os.getenv('CH_FREQ_WIDTH', null_int))
freq_step = int(os.getenv('CH_FREQ_STEP', null_int))
vis_dirs = os.getenv('CH_VIS_DIR', null_str) + '/%s' % run_id
vis_bk_dirs = os.getenv('CH_VIS_BK_DIR', null_str) + '/%s' % run_id
casa_workdir = os.getenv('CH_CASA_WORK_DIR', null_str)
num_jobs = int(os.getenv('CH_NUM_JOB', null_int))
target_field = (os.getenv('CH_TARGET_FIELD', null_str))

split_tmout = int(os.getenv('CH_SPLIT_TIMEOUT', null_int))
if (-1 == split_tmout):
    split_tmout = 3600
clean_tmout = int(os.getenv('CH_CLEAN_TIMEOUT', null_int))
if (-1 == clean_tmout):
    clean_tmout = 3600

bkp_split = int(os.getenv('CH_BKP_SPLIT', '0'))
sel_freq = int(os.getenv('CH_SLCT_FREQ', '1'))

#
cube_dir = os.getenv('CH_CUBE_DIR', null_str) + '/%s/' % run_id
out_dir = os.getenv('CH_OUT_DIR', null_str) + '/%s/' % run_id

check_dir(vis_dirs)
check_dir(vis_bk_dirs)
check_dir(cube_dir)
check_dir(out_dir)

# '/mnt/hidata/chiles/cubes/comb_1255~1280.image'
outname = '%s/comb_%d~%d.image' % (out_dir, freq_min, freq_max)

obs_list, all_obs = getMyObs(job_id, obs_dir, obs_first, obs_last, num_jobs)
obsId_list = []

print "myobs = \t%s\nvis_dirs = \t%s\nrun_id = \t%s" % (str(obs_list), vis_dirs, run_id)


for obs in obs_list:
    infile_dir = '%s/%s' % (obs_dir, obs)
    lsre = execCmd('ls %s' % infile_dir)

    infile = None
    for ff in lsre[1].split('\n'):
         if (ff.endswith(INPUT_VIS_SUFFIX)):
             infile = '%s/%s' % (infile_dir, ff)
    if (not infile):
        print 'No measurementSet file found under %s' % infile_dir
        continue

    obsId = os.path.basename(infile_dir).replace('_FINAL_PRODUCTS', '')
    obsId_list.append(obsId)
    outdir = '%s/%s/' % (vis_dirs, obsId)
    backup_dir = '%s/%s/' % (vis_bk_dirs, obsId)
    do_cvel(infile, outdir, backup_dir, freq_min,
             freq_max, freq_step, freq_width, spec_window, obsId)

done_obs = checkIfAllObsSplitDone(casa_workdir, job_id, run_id, all_obs, timeout = split_tmout)

vis_dirs_cube = []
for obsId in done_obs.keys():
    vis_dirs_cube.append('%s/%s/' % (vis_dirs, obsId))

do_cube(vis_dirs_cube, cube_dir, freq_min, freq_max, freq_step, freq_width, job_id, num_jobs, debug)

if (job_id == 0): # only the first job will do the final concatenation
    combineAllCubes(cube_dir,outname,freq_min,freq_max,freq_step,casa_workdir,
                    run_id, debug, timeout = clean_tmout)

