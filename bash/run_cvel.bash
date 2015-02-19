#  _   _  ___ _____ _____
# | \ | |/ _ \_   _| ____|
# |  \| | | | || | |  _|
# | |\  | |_| || | | |___
# |_| \_|\___/ |_| |_____|
#
# The disk setup is done in the setup_disks.bash script
#
# When this is run as a user data start up script is is run as root - BE CAREFUL!!!

# As we might need to wait for the mount point to arrive as it can only be attached
# after the instance is running
sleep 10
while [ ! -b "/dev/xvdf" ]; do
  echo Sleeping
  sleep 30
done

# Now mount the data disk
mkdir -p /mnt/Data/data1
mount /dev/xvdf /mnt/Data/data1
chmod -R oug+r /mnt/Data/data1

# Run the cvel pipeline
##### runuser -l ec2-user -c 'bash -vx /home/ec2-user/chiles_pipeline/bash/start_cvel.sh min_freq max_freq' #####
{0}

# Copy files to S3
runuser -l ec2-user -c 'python /home/ec2-user/chiles_pipeline/python/copy_cvel_output.py -p 2 {1}'

# Copy log files to S3
runuser -l ec2-user -c 'python /home/ec2-user/chiles_pipeline/python/copy_log_files.py -p 3 CVEL-logs/{1}'

# Unattach the volume and delete it
umount /dev/xvdf
sleep 10
runuser -l ec2-user -c 'python /home/ec2-user/chiles_pipeline/python/delete_volumes.py {2}'

# Terminate
shutdown -h now
