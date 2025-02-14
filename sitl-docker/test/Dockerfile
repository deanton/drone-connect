# Use Ubuntu 22.04 as base
FROM ubuntu:22.04

# Set non-interactive mode
ENV DEBIAN_FRONTEND=noninteractive

# # Install required dependencies
# RUN apt-get update && apt-get install -y \
#     python3 python3-pip git wget nano curl sudo screen tmux iproute2 net-tools netcat supervisor nftables \
#     && rm -rf /var/lib/apt/lists/*

USER root

# Add nftables rule to allow UDP traffic (Crucial! - Run as root in the same RUN command)
RUN apt-get update && apt-get install -y \
    python3 python3-pip git wget nano curl sudo screen tmux iproute2 net-tools netcat supervisor nftables lsb-release tzdata \
    && rm -rf /var/lib/apt/lists/*
    #&& nft add rule inet filter input udp dport 14551 accept  # Run as root in this RUN command

# Install MAVProxy, pymavlink, and Zenoh client
RUN pip3 install --no-cache-dir pymavlink mavproxy eclipse-zenoh empy==3.3.4 pexpect

# Create a non-root user 'ardupilot' and switch to it
RUN useradd -m -s /bin/bash ardupilot && \
    echo "ardupilot ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

#USER ardupilot
WORKDIR /home/ardupilot

#RUN sudo nft add rule inet filter input udp dport 14551 accept

# Clone ArduPilot repository
#RUN git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git /home/ardupilot/ardupilot
RUN git clone --depth=1 --recurse-submodules https://github.com/ArduPilot/ardupilot.git /home/ardupilot/ardupilot

# Ensure the 'ardupilot' user owns the entire ArduPilot directory
RUN chown -R ardupilot:ardupilot /home/ardupilot/ardupilot

USER root
RUN git config --global --add safe.directory /home/ardupilot/ardupilot
USER ardupilot 

WORKDIR /home/ardupilot/ardupilot

# Rin prerequisite installation separately 
#RUN bash Tools/environment_install/install-prereqs-ubuntu.sh -y && sudo usermod -a -G dialout ardupilot
ARG SKIP_AP_EXT_ENV=0
ARG SKIP_AP_GRAPHIC_ENV=1
ARG SKIP_AP_COV_ENV=1
ARG SKIP_AP_GIT_CHECK=1
ARG DO_AP_STM_ENV=1

RUN bash -c "SKIP_AP_EXT_ENV=$SKIP_AP_EXT_ENV SKIP_AP_GRAPHIC_ENV=$SKIP_AP_GRAPHIC_ENV SKIP_AP_COV_ENV=$SKIP_AP_COV_ENV SKIP_AP_GIT_CHECK=$SKIP_AP_GIT_CHECK \
    DO_AP_STM_ENV=$DO_AP_STM_ENV \
    AP_DOCKER_BUILD=1 Tools/environment_install/install-prereqs-ubuntu.sh -y || true" && sudo usermod -aG dialout ardupilot
#RUN bash -c "Tools/environment_install/install-prereqs-ubuntu.sh -y || true" && sudo usermod -aG dialout ardupilot

# Source profile and build SITL in a separate command
RUN /bin/bash -c "source ~/.profile && ./waf configure --board=sitl"
RUN /bin/bash -c "source ~/.profile && ./waf copter"
RUN /bin/bash -c "source ~/.profile && ./waf plane"
RUN /bin/bash -c "source ~/.profile && ./waf rover"

# Copy required files
COPY drone-communicator.py /home/ardupilot/drone-communicator.py
COPY entrypoint.sh /home/ardupilot/entrypoint.sh
COPY supervisord.conf /home/ardupilot/supervisord.conf

# Switch back to root for final setup
#USER root

# Make entrypoint script executable
RUN chmod +x /home/ardupilot/entrypoint.sh

# Expose MAVLink TCP Port
EXPOSE 5760
EXPOSE 14550/udp

# # Add iptables rule to allow UDP traffic (Crucial!)
# USER root
# #RUN iptables -A INPUT -p udp --dport 14551 -j ACCEPT
# RUN nft add rule inet filter input udp dport 14551 accept
# USER ardupilot

# Set entrypoint script
ENTRYPOINT ["/home/ardupilot/entrypoint.sh"]
#CMD ["/usr/bin/supervisord", "-c", "/home/ardupilot/supervisord.conf"]
