"""
Taken from makecube.py extracting the loop over cvel

This module should run together with the casapy: e.g. casapy --nologger -c loop_cvel.py
"""


execfile('/home/ec2-user/chiles_pipeline/python/makecube_defines.py')

print 'test'+INPUT_VIS_SUFFIX
# loop through selected obs and cvel. Uses obId to only do subset of possible

check_dir(job_id, vis_dirs)
check_dir(job_id, vis_bk_dirs)

obs_list, all_obs = getMyObs(job_id, obs_dir, obs_first, obs_last, num_jobs)
obsId_list = []

print "myobs = \t%s\nvis_dirs = \t%s\nrun_id = \t%s" % (str(obs_list), vis_dirs, run_id)


for obs in obs_list:
    infile_dir = '%s/%s' % (obs_dir, obs)
    lsre = execCmd('ls %s' % infile_dir)

    infile = None
    for ff in lsre[1].split('\n'):
        if ff.endswith(INPUT_VIS_SUFFIX):
            infile = '%s/%s' % (infile_dir, ff)
    if not infile:
        print 'No measurementSet file found under %s' % infile_dir
        continue

    obsId = os.path.basename(infile_dir).replace('_FINAL_PRODUCTS', '')
    obsId_list.append(obsId)
    outdir = '%s/%s/' % (vis_dirs, obsId)
    backup_dir = '%s/%s/' % (vis_bk_dirs, obsId)
    do_cvel(infile, outdir, backup_dir, freq_min,
             freq_max, freq_step, freq_width, spec_window, obsId)

