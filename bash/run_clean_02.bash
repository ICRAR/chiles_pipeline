#  _   _  ___ _____ _____
# | \ | |/ _ \_   _| ____|
# |  \| | | | || | |  _|
# | |\  | |_| || | | |___
# |_| \_|\___/ |_| |_____|
#
# The disk setup is done in the setup_disks.bash script
#
# When this is run as a user data start up script it is run as root - BE CAREFUL!!!

# Clean uses a lot of memory so make a swap on the disk
/bin/dd if=/dev/zero of=/mnt/output/swapfile bs=1G count={3}
chown root:root /mnt/output/swapfile
chmod 600 /mnt/output/swapfile
/sbin/mkswap /mnt/output/swapfile
/sbin/swapon /mnt/output/swapfile

# We need lots and lots of files open for the clean process
ulimit -n 8192

# Install the latest versions of the Python libraries and pull the latest code
pip install {4}
cd /home/ec2-user/chiles_pipeline
runuser -l ec2-user -c '(cd /home/ec2-user/chiles_pipeline ; git pull)'

# Copy files from S3
runuser -l ec2-user -c 'python /home/ec2-user/chiles_pipeline/python/copy_clean_input.py {0} -p 4'

# Log the disk usage
df -h

# Run the clean pipeline
runuser -l ec2-user -c 'bash -vx /home/ec2-user/chiles_pipeline/bash/start_clean_02.sh {1} {2} 1'
runuser -l ec2-user -c 'bash -vx /home/ec2-user/chiles_pipeline/bash/start_clean_02.sh {1} {2} 2'
runuser -l ec2-user -c 'bash -vx /home/ec2-user/chiles_pipeline/bash/start_clean_02.sh {1} {2} 4'
runuser -l ec2-user -c 'bash -vx /home/ec2-user/chiles_pipeline/bash/start_clean_02.sh {1} {2} 8'
runuser -l ec2-user -c 'bash -vx /home/ec2-user/chiles_pipeline/bash/start_clean_02.sh {1} {2} 16'
runuser -l ec2-user -c 'bash -vx /home/ec2-user/chiles_pipeline/bash/start_clean_02.sh {1} {2} 32'

# Log the disk usage
df -h

# Copy files to S3
runuser -l ec2-user -c 'python /home/ec2-user/chiles_pipeline/python/copy_clean_02_output.py {0}'

# Copy files to S3
runuser -l ec2-user -c 'python /home/ec2-user/chiles_pipeline/python/copy_log_files.py -p 3 CLEAN_02-log/{0}'

# Terminate
#shutdown -h now
