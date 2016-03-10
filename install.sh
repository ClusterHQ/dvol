#!/bin/sh
# Support parameter for which tag to use
TAG=${1:-latest}
# Kill existing plugin if it exists
docker rm -f dvol-docker-plugin || true
# Run the dvol docker plugin
docker run -v /var/lib/dvol:/var/lib/dvol --restart=always -d \
    -v /run/docker/plugins:/run/docker/plugins \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --name=dvol-docker-plugin clusterhq/dvol:${TAG}
# Create a local shell script wrapper to run dvol
cat > dvol.sh <<EOF
#!/bin/sh
docker run --rm -ti -v /var/lib/dvol:/var/lib/dvol \\
    -v /run/docker/plugins:/run/docker/plugins \\
    -v /var/run/docker.sock:/var/run/docker.sock \\
    -v \${PWD}:/pwd \\
    clusterhq/dvol:${TAG} dvol "\$@" 2>/dev/null
EOF
# Install it
sudo mv dvol.sh /usr/local/bin/dvol
sudo chmod +x /usr/local/bin/dvol
