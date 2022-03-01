Changelog
=========

## Version 0.5.0b
 - Removed all code running at install time. Pyrrowhead will no instead look for a
   `~/.pyrrowhead` directory and initialize the directory if it doesn't exist.
 - Added command `pyrrowhead cloud client-add` so client systems can be added to the
   cloud config without having to edit it manually.
 - All code is now formatted with Black.

## Version 0.4.0b
 - Now considered to be a beta release.
 - Updated dependencies, installation should now work without issues.
 - Restructured the repository to use an `src/` style.
 - Remove option to choose default cloud installation directory during installation.

## Version 0.3.0a

 - System query is now supported when the System registry is present.
 - Services can be inspected to get more information.
 - Orchestration and authorization rules can be listed, added and removed in the same way services can. 
 - Setup and installation now set up the docker subnetwork and container ip addresses.
 - Upon installation, the user will be asked where to install Arrowhead local clouds by default.
 