#!/bin/bash -vx
# When this is run as a user data start up script is is run as root - BE CAREFUL!!!
# Setup the ephemeral disk
if [ -b "/dev/xvdb" ]; then
  if mountpoint -q "/media/ephemeral0" ; then
    # The ephemeral disk is mounted on /media/ephemeral0
    rm -f /mnt/output
    ln -s /media/ephemeral0 /mnt/output
  else
    mkdir -p /mnt/output
    mkfs.ext4 /dev/xvdb
    mount /dev/xvdb /mnt/output
  fi
fi
chmod oug+wrx /mnt/output

# Wait for the boto file to be created
while [ ! -f "/home/ec2-user/.boto" ]; do
  echo Sleeping
  sleep 30
done
sleep 5

# We need lots and lots of files open for the clean process
ulimit -n 8196

# Copy files from S3
runuser -l ec2-user -c 'python /home/ec2-user/chiles_pipeline/python/copy_clean_input.py {0} -p 4'

# Run the clean pipeline
runuser -l ec2-user -c 'bash -vx /home/ec2-user/chiles_pipeline/bash/start_clean.sh {1} {2}'

# Copy files to S3
runuser -l ec2-user -c 'python /home/ec2-user/chiles_pipeline/python/copy_clean_output.py -p 3 {0}'

# Copy files to S3
runuser -l ec2-user -c 'python /home/ec2-user/chiles_pipeline/python/copy_log_files.py -p 3 CLEAN-log/{0}'

# Terminate
shutdown -h now
