import select

'''
Paramiko library has an old bug where reading the stdout hangs at times. This is a better implementation
of reading stdout than what is offered by Paramiko. Copied from stackoverflow.
Reference: https://stackoverflow.com/questions/23504126/do-you-have-to-check-exit-status-ready-if-you-are-going-to-check-recv-ready/32758464#32758464
'''


def custom_exec_command(ssh, cmd, timeout, want_exitcode=False):
    # one channel per command
    stdin, stdout, stderr = ssh.exec_command(cmd)
    # get the shared channel for stdout/stderr/stdin
    channel = stdout.channel

    # we do not need stdin.
    stdin.close()
    # indicate that we're not going to write to that channel anymore
    channel.shutdown_write()

    # read stdout/stderr in order to prevent read block hangs
    stdout_chunks = []
    stdout_chunks.append(stdout.channel.recv(len(stdout.channel.in_buffer)).decode())
    # chunked read to prevent stalls
    while not channel.closed or channel.recv_ready() or channel.recv_stderr_ready():
        # stop if channel was closed prematurely, and there is no data in the buffers.
        got_chunk = False
        readq, _, _ = select.select([stdout.channel], [], [], timeout)
        for c in readq:
            if c.recv_ready():
                stdout_chunks.append(stdout.channel.recv(len(c.in_buffer)).decode())
                got_chunk = True
            if c.recv_stderr_ready():
                # make sure to read stderr to prevent stall
                stderr.channel.recv_stderr(len(c.in_stderr_buffer))
                got_chunk = True
        '''
        1) make sure that there are at least 2 cycles with no data in the input buffers in order to not exit too early (i.e. cat on a >200k file).
        2) if no data arrived in the last loop, check if we already received the exit code
        3) check if input buffers are empty
        4) exit the loop
        '''
        if not got_chunk \
                and stdout.channel.exit_status_ready() \
                and not stderr.channel.recv_stderr_ready() \
                and not stdout.channel.recv_ready():
            # indicate that we're not going to read from this channel anymore
            stdout.channel.shutdown_read()
            # close the channel
            stdout.channel.close()
            break  # exit as remote side is finished and our bufferes are empty

    # close all the pseudofiles
    stdout.close()
    stderr.close()

    if want_exitcode:
        # exit code is always ready at this point
        return (''.join(stdout_chunks), stdout.channel.recv_exit_status())
    return ''.join(stdout_chunks)
