## Installation via the `x-road_rest_client_example_deploy.sh` Script

To automate the installation process and further operation of the web client, a script named `x-road_rest_client_example_deploy.sh` was created.

**This script:**

1. Installs the system software dependencies required for the web client.
2. Clones the repository.
3. Creates and activates a virtual environment.
4. Installs Python dependencies.
5. Creates a systemd service file to launch the web client.

**To install the web client using the script, follow these steps:**

1. Download the script:
```bash
wget https://raw.githubusercontent.com/fortor48/X-Road_REST_client_example/refs/heads/master/x-road_rest_client_example_deploy.sh
```

2. Make the file executable:
```bash
chmod +x x-road_rest_client_example_deploy.sh
```

3. Run the script:
```bash
./x-road_rest_client_example_deploy.sh
```

4. Navigate to the client directory:
```bash
cd X-Road_REST_client_example
```

5. Configure the web client according to the [configuration guide](./configuration.md).

Administration of the web client is carried out according to the [web service administration guide](/README.md#client-administration).

##

Materials created with support from the EU Technical Assistance Project "Bangladesh e-governance (BGD)".