# MLClient Developer Workspace

## Setup environment

1. Install docker
    ```shell
    # Set up the repository
    sudo apt-get update
    sudo apt-get install \
        apt-transport-https \
        ca-certificates \
        curl \
        software-properties-common \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    
    # Set up the stable repository
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
    
    # Install Docker Engine
    sudo apt-get install docker-ce docker-ce-cli
   
    # Add user to the 'docker' group
    sudo usermod -aG docker $(USER)
    
    # Enable and start Docker service
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # Output the version of Docker installed
    docker --version
    ```

2. Install docker compose
   
    ```shell
    # Update the package index
    sudo apt-get update

    # Install Docker Compose plugin
    sudo apt-get install docker-compose-plugin
    
    # Verify installation
    docker compose version
    ```

3. Build containers

   ```shell
   docker compose up -d
   docker compose exec -it dev sh -c "cd /mlclient && poetry install"
   ```

4. Run mlclient in an isolated container within a network

   ```shell
   docker compose exec dev bash
   cd /mlclient && poetry shell
   ```