ARG BUILD_FROM
FROM $BUILD_FROM

# Install required packages
RUN apk add --no-cache python3 py3-pip libusb

# Set the working directory
WORKDIR /usr/src/app

# Copy your application files
COPY vu1_dial_ha/ ./vu1_dial_ha/
COPY VU-Server/ ./VU-Server/
COPY run.sh .
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Make run.sh executable
RUN chmod a+x run.sh

# Set Python path to include VU-Server
ENV PYTHONPATH="${PYTHONPATH}:/usr/src/app/VU-Server"

# Command to run the application
CMD [ "./run.sh" ]