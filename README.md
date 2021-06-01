# Pyrrowhead - The CLI local cloud management tool!

Pyrrowhead is a work-in-progress command line tool for managing local clouds.

It currently provides functionalities for setup, installation/uninstallation and configuration of local clouds.

Install it with `pip install pyrrowhead` and try it out with
```shell
pyrrowhead --help
```

This tool is designed to use the Arrowhead docker containers and is currently only tested locally on Ubuntu.

## Functionalities

Before trying these steps, please create and go to an empty directory.

### Setup

Set up a local cloud configuration file with 
```shell
pyrrowhead setup <local cloud directory> <cloud name> <company name>
```

### Installation

Then install the local cloud with
```shell
pyrrowhead install cloud_config.yaml
```

### Configuration

Change local cloud to run in insecure mode with
```shell
pyrrowhead configure --disable-ssl
```

### Starting the cloud

Run local cloud with docker-compose
```shell
docker-compose up -d
```

### Stopping the cloud

Stop the cloud with docker-compose again
```shell
docker-compose down
```

### Uninstallation

When finished, uninstall the local cloud
```shell
pyrrowhead uninstall .
```