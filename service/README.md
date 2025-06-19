# Running PheWeb 2.0 API as a service
You can run the PheWeb 2.0 API as a service on your machine. Here we provide a quick tutorial about how you can set up the service file and run it. We will walk through the setup process on Ubuntu as an example.


## Setting the service
Once you've set up the API as shown in the main README, you can generate a service file to run the app on your machine.
**Note: you need sudo permission to set up the service file.**
We've created an example service file called `pheweb-api.service` in this directory. 

Once you've set up the service file, you initiate the service by running
```
# copy your service file to the correct dir
sudo cp pheweb-api.service /etc/systemd/system/pheweb-api.service 

# reload systemd setting
sudo systemctl daemon-reload 

# auto-start the service when the machine is turned on
sudo systemctl enable pheweb-api.service 

# start the service
sudo systemctl start pheweb-api.service 
```
To check the status of your pheweb service, run
```
sudo systemctl status pheweb-api.service
```
To check the log, run
```
journalctl -u pheweb-api.service
```

**Note: you can run the PheWeb 2.0 in a similar way by replacing the command in `ExecStart=` in the service file**

## Setting auto-mounted s3 bucket
If you are using s3 bucket to store the data, you can set it up to be auto-mounted by add one line in the `/etc/fstab`
```
s3fs#pheweb /mnt/s3 fuse _netdev,allow_other,passwd_file=/path/to/your/password,url=https://your/url/,use_cache=/tmp 0 0
```