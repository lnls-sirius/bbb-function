# Beaglebone Black - Function Detection and Applications
Scripts directly related to the beaglebone black with the following structure:
```
.
├── src
│   └── scripts
└── services
```
The `function` folder contains all scripts used to identify which device is connected to the beaglebone black.<br>

The `services` folder contains the service file related to the `function` applications.<br>

To install dependencies:
```
    make dependencies
```

To install:
```
    make install
```

To uninstall:
```
    make uninstall
```


## Beaglebone Black Function
Detect what is connected to the board and take the corresponding action.



## Beaglebone Black Rsync Client
Using rsync package to synchronize files and libraries used by Controls Group in its Beaglebones.
The rsync daemon must run on a server ($RSYNC_SERVER), which must contain all files up to date.

For libraries, files are syncronized and library rebuilded automatically.

### Running rsync_beaglebone.sh
Rsync updates one project by now.
Call the script with project name as argument: `./rsync_beaglebone.sh project-name` 

### rsync_beaglebone.sh steps
- Check whether server is up
- Check if there are updates available for current project
- If so, update files and rebuild libraries (if needed)
