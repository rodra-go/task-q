# Deploy the system
docker-compose up -d

# Create SSH Key
ssh-keygen -t rsa -b 2048

# Copy the Container's SSH Key to the host
ssh-copy-id <user_at_host>@$(hostname)

# Execute script on host
SCRIPT="sleep 10 && echo 'The End'"
ssh -l <user_at_host> $(hostname) "$SCRIPT"
