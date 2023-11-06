#!/usr/bin/env python

from collections import OrderedDict
import logging
import os
import shutil
import subprocess
import sys

import find_ec2

logger = logging.getLogger(__name__)

DEFAULT_PS1 = (
    "\\[\033[36m\\]{instance_name}\\[\033[0m\\] "
    "\\W \\[\033[33m\\]\\$\\[\033[0m\\] "
)
REMOTE_PS1_SCRIPT_PATH = ".ec2-connect/remote-ps1.sh"


# TODO: Move to a lib
def fzf(options, write_option, prompt="Select: ", multi=False):
    """
    Use fzf to filter options down. Options may be a list of any type of
    object, and write_option will be used to write them as a string. Options
    must produce unique strings so that the original objects can be matched
    back once fzf has selected them.
    """
    if not options:
        raise Exception("No options provided to fzf")

    fzf_exec = shutil.which("fzf")

    if not fzf_exec:
        raise Exception("Please install fzf to use this script")

    values = OrderedDict([(write_option(o), o) for o in options])
    if len(values) != len(options):
        raise ValueError(
            "Some options passed to fzf produced colliding strings!"
        )

    multi_flag = "-m" if multi else "+m"
    cmd = [fzf_exec, "--ansi", "-i", "-0", "--prompt", prompt, multi_flag]

    result = subprocess.run(
        cmd, input="\n".join(values.keys()), text=True, stdout=subprocess.PIPE
    )
    if result.returncode != 0:
        if result.stderr:
            logging.error(result.stderr)
        raise ValueError(f"fzf exited with return code {result.returncode}")

    lines = result.stdout.split("\n")
    return [values[line] for line in lines if line]


def _notice(msg, *args, **kwargs):
    logger.info(f"\033[33m{msg}\033[0m", *args, **kwargs)  # yellow


class Ec2Connect:
    """Handle connecting to an instance via SSH / SCP"""
    def __init__(self, host, user, key, command=None, scp=False):
        self.host = host
        self.user = user
        self.key = key
        self.command = command
        self.scp = scp

    def _get_ps1(self, instance_name):
        """
        Respect a custom PS1-providing executable where available
        """
        custom_ps1_exec = os.path.join(
            os.environ.get("HOME", ""),
            REMOTE_PS1_SCRIPT_PATH
        )
        if not os.path.isfile(custom_ps1_exec):
            return DEFAULT_PS1.format(instance_name=instance_name)

        cmd = [custom_ps1_exec, instance_name]

        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE)
        return result.stdout

    def get_command(self, instance_name):
        """
        Unless given a specific command to run, we do some clever juggling
        of a custom bashrc, use it to set a prettier PS1, and then start bash
        with that new --rcfile
        """
        if self.command:
            return self.command

        ps1 = self._get_ps1(instance_name)
        return (
            "cp ~/.bashrc ~/.bashrc.n && "
            f"echo 'export PS1=\"{ps1}\"' >> ~/.bashrc.n; "
            "bash --rcfile ~/.bashrc.n"
        )

    def print_scp(self, host):
        print(f"scp -i '{self.key}' $LOCAL_FILE {self.user}@{host}:~")

    def ssh(self, host, instance_name):
        _notice("Connecting to instance %s (%s)", instance_name, host)
        launch_cmd = self.get_command(instance_name)

        cmd = ["ssh", "-t", "-i", self.key, f"{self.user}@{host}", launch_cmd]
        subprocess.run(cmd)

    def connect(self, host, instance_name):
        if self.scp:
            return self.print_scp(host)

        return self.ssh(host, instance_name)


class Ec2ConnectTask:
    """
    The overall task of finding and filtering instances and then attempting to
    connect to one
    """
    def __init__(self, connect, finder, formatter, filter, ip_type):
        self.connect = connect
        self.finder = finder
        self.formatter = formatter
        self.filter = filter
        self.ip_type = ip_type or find_ec2.IP_PRIVATE

    def select_instance_ip(self):
        """
        Select instances interactively, using fzf if multiple match

        Retrieve the selected IP to connect to, and the associated instance.
        Note that depending on `ip_type` we may be selecting one of multiple IP
        choices for a given host, which is why we need to provide the selected
        IP as well

        :returns: Tuple (instance, ip_address)
        """
        instances = self.filter.apply(self.finder.get_all_instances())
        options = [
            (instance, ip)
            for instance in instances
            for ip in instance.get_ips_by_type(self.ip_type)
        ]

        if not options:
            raise ValueError("No results")

        if len(options) == 1:
            return options[0]

        return fzf(
            options=options,
            write_option=lambda o: self.formatter.format_line(o[0], o[1]),
            prompt="Select host: ",
            multi=False
        )[0]

    def run(self, override_host=None):
        host = None
        instance_name = None

        if override_host:
            host = override_host
            instance_name = f"host:{host}"
        else:
            instance, host = self.select_instance_ip()
            instance_name = instance.name

        if not host:
            raise ValueError("Can't connect to host with no IP available")

        self.connect.connect(host, instance_name)


def main():
    parser = find_ec2.get_argument_parser("ec2-connect")
    conn_parser = parser.add_argument_group("connection")
    conn_parser.add_argument(
        "-k", "--key",
        default=os.environ.get("EC2_CONNECT_DEFAULT_KEY", "$HOME/.ssh/id_rsa"),
        help="Use the specified SSH key"
    )
    conn_parser.add_argument(
        "--host", "--ip", dest="host", help=(
            "Do not look up IPs, just connect to the given IP "
            "or hostname instead"
        )
    )
    conn_parser.add_argument(
        "--scp", action="store_true", help=(
            "Instead of connecting to the host, print an scp command which "
            "can easily be used to copy files to/from the host"
        )
    )
    conn_parser.add_argument(
        "-u", "--user",
        default=os.environ.get("EC2_CONNECT_DEFAULT_USER", "ec2-user"),
        help="Use the specified user"
    )
    conn_parser.add_argument(
        "--cmd", help="Run the provided command instead of a bash shell"
    )

    args = parser.parse_args()

    logging.basicConfig(format="%(message)s")
    logger.setLevel(logging.INFO)

    connect = Ec2Connect(
        host=args.host, user=args.user, key=args.key, command=args.cmd,
        scp=args.scp
    )
    finder, formatter, filter = find_ec2.create_components(args)
    task = Ec2ConnectTask(connect, finder, formatter, filter, args.ip_type)

    try:
        task.run(override_host=args.host)
    except ValueError as e:
        logging.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
