ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python (for running VU-Server) and any needed libs
RUN apk add --no-cache python3 py3-pip

# Copy VU-Server source code into the image
COPY ../vu-server /opt/vu-server

# Install VU-Server Python dependencies
RUN pip3 install -r /opt/vu-server/requirements.txt

# Copy and set up the run script
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# Expose VU-Server API port
EXPOSE 5340

CMD [ "/run.sh" ]
