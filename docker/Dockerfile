FROM nvcr.io/nvidia/isaac-sim:4.2.0

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /workspace


RUN apt-get update && apt-get install -y \
    git wget curl ffmpeg build-essential cmake pkg-config \
    libgl1 libglib2.0-0 python3-pip python3-dev \
    lsb-release gnupg2 software-properties-common \
    && rm -rf /var/lib/apt/lists/*


RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add -
RUN echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/ros2.list


RUN apt-get update && apt-get install -y \
    ros-humble-desktop \
    python3-colcon-common-extensions \
    python3-rosdep python3-vcstool \
    ros-humble-cv-bridge ros-humble-image-transport \
    ros-humble-vision-msgs ros-humble-sensor-msgs \
    && rm -rf /var/lib/apt/lists/*


RUN apt-get update && apt-get install --reinstall -y ros-humble-cv-bridge \
    && rm -rf /var/lib/apt/lists/*


RUN rosdep init || true && rosdep update


COPY requirements-ros.txt .
RUN pip3 install --upgrade pip
RUN pip3 install --ignore-installed sympy -r requirements-ros.txt


COPY requirements.txt .
RUN /isaac-sim/python.sh -m pip install --upgrade pip
RUN /isaac-sim/python.sh -m pip install -r requirements.txt


COPY . /workspace


RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "export PYTHONPATH=/workspace:/workspace/MiDaS:\$PYTHONPATH" >> ~/.bashrc


WORKDIR /workspace/ros2_ws
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build --symlink-install" || true

WORKDIR /workspace


# Entrypoint

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]