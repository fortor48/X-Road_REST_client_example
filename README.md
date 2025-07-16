# Synchronous REST Client with Support for the X-Road System

## Client Description

The REST client described in this guide is developed in Python using the FastAPI framework and is compatible with the X-Road system.

FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.10+ based on standard asynchronous calls.

This client allows retrieving information about informational objects (users) and managing their status, including sending requests for searching, retrieving, creating, updating, and deleting objects to the respective service.

Additional features include uploading archives containing digitally signed request and response messages in ASiC container format, as well as generating keys and certificates for mutual authentication between the REST client and the X-Road system Security Server (ШБО).

To demonstrate integration with the X-Road system, a [web service](https://github.com/MadCat-88/Trembita_Py_R_SyncSrv) was developed to work with this web client.

## Software Requirements

| Software       | Version  | Notes                                                                                                                                                                                                       |
|:---------------|:--------:|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Ubuntu Server  |  24.04   | Recommended virtual machine specs:<br/> CPU: 1 <br/> RAM: 512 MB                                                                                                                                            |
| Python         | **3.10!**| Installed automatically via script.<br/> You may also install it manually depending on the installation method.<br/>**Important!** If the Python version is below 3.10, the client will not work.  |
| Git            |          | For cloning the repository                                                                                                                                                                                  |

## Dependencies

The software dependencies for the client are listed in the `requirements.txt` file.

## Project Structure

The project consists of the following files and directories:

```
X-Road_REST_client_example/
├── Dockerfile                    # Dockerfile for containerizing the application
├── LICENSE                       # License
├── README.Docker.md              # Documentation
├── README.md                     # Documentation
├── app.py                        # Application entry point
├── asic                          # Folder for storing ASiC containers with exchange results
├── certs                         # Folder for app key and certificate for HTTPS, and the X-Road Security Server certificate
│    ├── cert.pem
│    └── key.pem
├── compose.yaml
├── config.ini                    # Application configuration file
├── deploy.sh                     # Automatic installation script
├── docs                          # Documentation
│    ├── docker_installation.md   # Documentation
│    ├── manual_installation.md   # Documentation
│    └── script_installation.md   # Documentation
├── remove.sh                     # Automatic removal script
├── requirements.txt              # Application dependencies
├── templates                     # Folder with application webpage templates
│    ├── create_person.html       # Web page template
│    ├── error.html               # Web page template
│    ├── list_certs.html          # Web page template
│    ├── list_files.html          # Web page template
│    ├── list_person.html         # Web page template
│    ├── navbar.html              # Web page template
│    ├── search_form.html         # Web page template
│    └── user_form.html           # Web page template
└── utils.py                      # X-Road interaction library
```

## Client Installation

The client can be installed via an automatic installation script or manually. It can also run in Docker.

- [Client installation using the automatic installation script](./docs/script_installation.md).
- [Manual client installation](./docs/manual_installation.md).
- [Client configuration](./docs/configuration.md).
- [Running the web client in Docker](./docs/docker_installation.md).

## Client Administration

### Starting the Web Client

To start the web client, run the following command:

```bash
sudo systemctl start x-road_rest_client_example
```

### Accessing the Web Client

To access the web interface of the client, go to:  
`http://<your_server_ip>:5000`

### Checking Web Client Status

To check the status of the web client, run:

```bash
sudo systemctl status x-road_rest_client_example
```

### Stopping the Web Client

To stop the web service, run:

```bash
sudo systemctl stop x-road_rest_client_example
```

### Removing the Web Client

A script `remove.sh` is provided to remove the web client and all related components.

When executed, the script will stop and remove the web client, delete the virtual environment, cloned repository, and system dependencies.

To run the script:

1. Make the file executable:

```bash
chmod +x remove.sh
```

2. Execute the script:

```bash
./remove.sh
```

### Viewing the Log

By default, the event log is stored in the file `/tmp/x-road_rest_client_example.log`.

Logging parameters are configured in the `config.ini` file. See [configuration guide](./docs/configuration.md) for details.

To view the web client's log:

```bash
journalctl -u x-road_rest_client_example -f
```

### HTTPS Configuration

To configure HTTPS communication with the X-Road Security Server:

1. Set the appropriate protocol in the config file (`config.ini`). See [configuration guide](./docs/configuration.md) for details.

2. Upload the client’s certificate (available in the "Certificates" tab in the web interface, file `cert.pem`) to the appropriate X-Road subsystem.

3. Upload the internal TLS certificate of the X-Road Security Server to the client’s certificate directory (by default: `/X-Road_REST_client_example/certs/`). See [configuration guide](./docs/configuration.md) for details.

**Important:** The web client supports only PEM format certificates.

## Web Client Integration with the X-Road System

For full integration with the X-Road system, the web client must be able to add HTTP headers to requests required for transmission through X-Road secure gateways.  
Additionally, for identifying messages in its own information system, the client must assign a unique identifier in the `Uxp-queryID` header for each request.  
More details on headers are provided in the [guide on working with REST services in the Trembita system](https://github.com/MadCat-88/Services-development-for-Trembita-system/blob/main/REST%20services%20development%20for%20Trembita%20system.md#%D0%B7%D0%B0%D0%B3%D0%BE%D0%BB%D0%BE%D0%B2%D0%BA%D0%B8-%D0%B7%D0%B0%D0%BF%D0%B8%D1%82%D1%96%D0%B2-%D0%B4%D0%BB%D1%8F-rest-%D1%81%D0%B5%D1%80%D0%B2%D1%96%D1%81%D1%96%D0%B2-%D0%BD%D0%B5%D0%BE%D0%B1%D1%85%D1%96%D0%B4%D0%BD%D1%96-%D0%B7%D0%B0%D0%B4%D0%BB%D1%8F-%D0%B7%D0%B0%D0%B1%D0%B5%D0%B7%D0%BF%D0%B5%D1%87%D0%B5%D0%BD%D0%BD%D1%8F-%D1%81%D1%83%D0%BC%D1%96%D1%81%D0%BD%D0%BE%D1%81%D1%82%D1%96-%D0%B7-%D1%81%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D0%BE%D1%8E-%D1%82%D1%80%D0%B5%D0%BC%D0%B1%D1%96%D1%82%D0%B0).

In this web client, header configuration is done via the `config.ini` file. See the [configuration guide](./docs/configuration.md) for detailed information.

## Using the Web Client

To access the web interface of the developed client, go to:

```
http://<your_server_ip>:5000
```

In this interface, you can:

1. Search for records in the database by specific parameters.  
2. Create records in the database.  
3. Modify database records.  

**Important!** Service limitation – the **unzr** field cannot be modified!

4. Delete records from the database using the UNZR field.  
5. If HTTPS is used for communication with the X-Road system, you can download ASiC containers with requests from the web client to the web service transmitted through the Security Server.  
6. Download the client’s certificate for mutual authentication with the Security Server. This can be done from the "Certificates" tab.

## Contributing

If you wish to contribute to the project, please fork the repository and submit a Pull Request.

## License

This project is licensed under the MIT License.

##

This material was developed with the support of the international technical assistance project "EU Support to the Digital Transformation of Ukraine (DT4UA)".