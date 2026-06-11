#!/usr/bin/with-contenv bashio
# ==============================================================================
# Take down the S6 supervision tree when the VU-Server service exits.
#
# With s6-overlay v3 a dying `run` script is restarted forever by default, so a
# fatal exit (e.g. run.sh giving up after MAX_RESTARTS) would crash-loop
# invisibly while Supervisor still shows the add-on as "running". This finish
# script records the exit code and halts the container instead, handing control
# back to Supervisor's restart policy / watchdog.
# ==============================================================================
readonly exit_code_service="${1}"
readonly exit_code_signal="${2}"

bashio::log.info \
    "Service VU-Server exited with code ${exit_code_service} (by signal ${exit_code_signal})."

# s6 reports a signal-kill as service code 256 with the signal number in $2;
# translate that to the conventional 128+signal container exit code.
if [[ "${exit_code_service}" -eq 256 ]]; then
    container_exit_code=$((128 + exit_code_signal))
    bashio::log.warning \
        "Service was terminated by signal ${exit_code_signal}; halting add-on."
else
    container_exit_code="${exit_code_service}"
    if [[ "${exit_code_service}" -ne 0 ]]; then
        bashio::log.warning \
            "Service exited with a non-zero status; halting add-on."
    fi
fi

# Record the exit code BEFORE halting — halt does not return — so Supervisor
# sees the real status, then bring the whole container down.
echo "${container_exit_code}" > /run/s6-linux-init-container-results/exitcode
exec /run/s6/basedir/bin/halt
