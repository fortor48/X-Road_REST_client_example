# 🛠️ Manual Client Installation

You can install the web client manually without using the installation script.

To begin, you need a clean Ubuntu system. All required packages and repositories will be set up during installation.

**To install this web client manually, follow these steps:**

### 1. Install required packages:

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv
```

**Note:** If your Python version is below 3.10, the client will not work.

### 2. Clone the repository

```bash
git clone https://github.com/fortor48/X-Road_REST_client_example.git
```

### 3. Navigate to the web client directory

```bash
cd X-Road_REST_client_example
```

### 4. Create a virtual environment
```bash
python3 -m venv venv
```

### 5. Activate the virtual environment
```bash
source venv/bin/activate
```

### 6. Install dependencies
```bash
pip install -r requirements.txt
```

### 7. Configure the web client according to the [configuration instructions](./configuration.md)

### 8. Create a systemd unit file for starting the web service:

```bash
sudo bash -c "cat > /etc/systemd/system/x-road_rest_client_example.service" << EOL
[Unit]
Description=Flask Application
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL
```

### 9. Reload systemd configuration:

```bash
sudo systemctl daemon-reload
```

### 10. Enable service to start automatically

```bash
sudo systemctl enable x-road_rest_client_example
```

Administration of the web client should follow the [web service administration guidelines](/README.md#client-administration)

##
The materials were created with support from the international technical assistance project “Bangladesh e-governance (BGD)”.
