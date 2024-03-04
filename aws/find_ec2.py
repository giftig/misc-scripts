#!/usr/bin/python3

import argparse
import datetime
import json
import math
import os
from typing import Optional

import boto3
from botocore import session as core_session
from botocore.credentials import JSONFileCache

# Internal enum for which IPs to present
IP_PUBLIC = "public_ip"
IP_PRIVATE = "private_ip"
IP_ALT = "alternate_ip"

# EC2 instance state codes
STATE_PENDING = 0
STATE_RUNNING = 16
STATE_SHUTTING_DOWN = 32
STATE_TERMINATED = 48
STATE_STOPPING = 64
STATE_STOPPED = 80

# Icons to express state in few characters
STATE_ICONS = {
    STATE_PENDING: "⌛",
    STATE_RUNNING: "✅",
    STATE_STOPPING: "🚫⌛",
    STATE_STOPPED: "🚫",
    STATE_SHUTTING_DOWN: "💀⌛",
    STATE_TERMINATED: "💀"
}

# Fields (format keys)
INSTANCE_ID = "instance_id"
IP = "ip"
NAME = "name"
UPTIME = "uptime"

DEFAULT_FIELDS = [NAME, IP, INSTANCE_ID]
ALL_FORMAT_FIELDS = [INSTANCE_ID, IP, NAME, UPTIME]

# Approx. expected lengths of fields for pretty printing with printf
PRETTY_LENGTHS = {
    INSTANCE_ID: 21,
    IP: 15,
    NAME: 34,
    UPTIME: 7
}

# Mark fields missing like (no name) if absent
MARK_ABSENT_FIELDS = {NAME}

# Replace with an empty string if absent
OMIT_ABSENT_FIELDS = {IP}

# Potential output formats enum
OUTPUT_PRETTY = "pretty"
OUTPUT_CSV = "csv"


def get_argument_parser(name="find_ec2"):
    """
    Get the argument parser. This is extracted out so that derived scripts can
    easily inherit all the options needed to work with this script

    N.B. this could also be done via parser inheritance (parents=*) but would
    require add_help=False in the root and splitting our parser into two, so
    this approach is slightly simpler for the moment.
    """
    parser = argparse.ArgumentParser(name)
    parser.add_argument(
        "-C", "--no-cache", action="store_false", dest="use_cache",
        help="Skip the cache"
    )
    parser.add_argument(
        "pattern", nargs="?", help=(
            "Filter instances by this term before presenting choices. If "
            "there is exactly one match for the term it will be picked "
            "automatically."
        )
    )

    format_parser = parser.add_argument_group("format")
    format_parser.add_argument(
        "--format-key", default=None,
        help=(
            "Specify fields to include in the output, as comma-separated "
            "values. The following fields are currently supported "
            f"(case-insensitive): {','.join(ALL_FORMAT_FIELDS)}. Default is "
            f"{','.join(DEFAULT_FIELDS)},{UPTIME}"
        )
    )
    format_parser.add_argument(
        "--csv", dest="output_format", nargs="?", const=OUTPUT_CSV,
        help="Output data as CSV instead of pretty-printing"
    )
    format_parser.add_argument(
        "--public-ip", action="store_const", dest="ip_type", const=IP_PUBLIC,
        help="Use public IP instead of private"
    )
    format_parser.add_argument(
        "-a", "--alt-ip", action="store_const", dest="ip_type", const=IP_ALT,
        help=(
            "Find alternate IPs of instances only. Lists each non-default IP "
            "of an instance as a separate entry, and excludes the primary IP"
        )
    )
    format_parser.add_argument(
        "-U", "--no-uptime", action="store_false", dest="show_uptime",
        help=(
            "Exclude instance uptime from display. Equivalent to "
            f"--format-key {','.join(DEFAULT_FIELDS)}"
        )
    )
    return parser


def serialise_json(obj: any) -> str:
    """Serialiser for non-serialisable types"""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    raise ValueError(f"Don't know how to serialise {obj}, type {type(obj)}")


class Ec2Instance:
    def __init__(self, data):
        self.data = data

        self.name = None

        tags = data.get("Tags", [])
        for t in tags:
            if t["Key"] == "Name":
                self.name = t["Value"]

        self.instance_id = data["InstanceId"]
        self.launch_time = datetime.datetime.fromisoformat(data["LaunchTime"])
        self.state = data["State"]["Name"]
        self.state_code = data["State"]["Code"]
        self.private_ip = data.get("PrivateIpAddress")
        self.public_ip = data.get("PublicIpAddress")

    def get_ips_by_type(self, ip_type):
        if ip_type == IP_PRIVATE:
            return [self.private_ip]

        if ip_type == IP_PUBLIC:
            return [self.public_ip]

        if ip_type == IP_ALT:
            return self.alternate_ips

        return []

    @property
    def alternate_ips(self):
        ips = []

        interfaces = self.data.get("NetworkInterfaces", [])
        for interface in interfaces:
            ip = interface.get("PrivateIpAddress")

            if ip is not None and ip != self.private_ip:
                ips.append(ip)

        return ips

    @property
    def uptime(self):
        now = datetime.datetime.now(datetime.UTC)
        launch_time = self.launch_time

        return (now - launch_time).total_seconds()

    def __str__(self):
        return f"{self.name}\t{self.private_ip}\t{self.instance_id}"

    def __gt__(self, other):
        my_key = [self.name or "", self.private_ip or "", self.instance_id]
        other_key = [
            other.name or "", other.private_ip or "", other.instance_id
        ]

        return my_key > other_key


class Ec2InstanceFormatter:
    def __init__(
        self, format_key, ip_type=IP_PRIVATE, output_format=OUTPUT_PRETTY
    ):
        self.ip_type = ip_type

        self.format_key = format_key
        self.output_format = output_format

        for field in self.format_key:
            if field not in ALL_FORMAT_FIELDS:
                raise ValueError(
                    f"'{field}' is not a valid option for format key"
                )

    def format_field(self, key, instance, value=None):
        """Prettify different fields in different ways based on key"""
        value = value or getattr(instance, key, None)

        if key in MARK_ABSENT_FIELDS:
            return value or f"(no {key})"

        if key in OMIT_ABSENT_FIELDS:
            return value or ""

        if key == UPTIME:
            return self.format_uptime(instance)

        return value

    def format_uptime(self, instance):
        uptime = instance.uptime
        units = "s"

        thresholds = [("m", 60), ("h", 60), ("d", 60)]

        for unit, threshold in thresholds:
            if not uptime > threshold:
                break

            uptime /= threshold
            units = unit

        # TODO: colourise?
        pretty_uptime = f"{math.floor(uptime)}{units}"
        pretty_state = STATE_ICONS[instance.state_code]

        return f"{pretty_state} {pretty_uptime}"

    def format_line(self, instance, ip):
        """
        One line of output format, specifying an IP to display along with the
        instance. With --alt-ip, Where an
        instance has multiple IPs associated and we want to see all of them,
        such as with --alt-ip, we will emit multiple records, one for each IP.

        In cases, IP may be expected to be absent for some entries.
        """
        line = []
        sep = "," if self.output_format == OUTPUT_CSV else " "

        for key in self.format_key:
            formatted = self.format_field(
                key, instance, value=ip if key == IP else None
            )

            # Pad to a given width if we're creating human-readable output
            if self.output_format == OUTPUT_PRETTY:
                len = PRETTY_LENGTHS.get(key, 1)
                line.append(f"{formatted : <{len}}")
            else:
                line.append(formatted)

        return sep.join(line)

    def format(self, instance) -> Optional[str]:
        ips = instance.get_ips_by_type(self.ip_type)

        lines = [
            self.format_line(instance, ip)
            for ip in ips
        ]
        if not lines:
            return None

        return "\n".join(lines)


class Ec2InstanceFinder:
    tmp_dir = "/tmp"

    def __init__(self, use_cache=True):
        self.session = self.create_session()
        self.ec2 = self.session.client("ec2")
        self.use_cache = use_cache

    @staticmethod
    def create_session():
        """
        Create a boto session which reuses the aws cli's credential cache on disk
        """
        cache_file = os.path.join(os.path.expanduser("~"), ".aws/cli/cache")
        sess = core_session.get_session()
        sess.get_component("credential_provider").get_provider("assume-role").cache = (
            JSONFileCache(cache_file)
        )
        return boto3.Session(botocore_session=sess)

    @property
    def cache_key(self) -> str:
        access_key = os.environ.get("AWS_ACCESS_KEY_ID", "defaultaccesskey")
        profile = self.session.profile_name or "default-profile"
        today = datetime.datetime.today().strftime("%Y-%m-%d")

        return (
            f"find-ec2-results-{access_key}-{profile}-{today}.json"
        )

    @property
    def cache_file(self) -> str:
        return os.path.join(self.tmp_dir, self.cache_key)

    def write_cache(self, data):
        with open(self.cache_file, "w") as f:
            json.dump(data, f, default=serialise_json)

    def read_cache(self):
        if not os.path.isfile(self.cache_file):
            return None

        with open(self.cache_file, "r") as f:
            return json.load(f)

    def get_results(self):
        if self.use_cache:
            data = self.read_cache()

            if data is not None:
                self.data = data
                return self.data

        response = self.ec2.describe_instances()

        # Pass the data in and out of the cache first as we will lose type
        # information for datetimes when we serialise it, so this makes sure
        # we have it in a consistent format
        self.write_cache(response)
        self.data = self.read_cache()

        return self.data

    def get_all_instances(self):
        results = self.get_results()
        return sorted([
            Ec2Instance(i)
            for r in results["Reservations"] for i in r["Instances"]
        ])


class Ec2InstanceFilter:
    """
    Just filter instances according to pattern config
    """
    def __init__(self, pattern):
        self.pattern = pattern

    def apply(self, instances):
        if not self.pattern:
            return instances

        return [
            i for i in instances
            if i.name and (
                self.pattern in i.name or self.pattern in i.instance_id
            )
        ]


def create_components(args):
    """
    Create the finder, formatter and filter components from the provided args.
    Again this makes it easier to reuse the logic of constructing these from
    common argparse components.

    This also validates some of the arguments in doing so.
    """
    format_key = (
        args.format_key.split(",") if args.format_key else DEFAULT_FIELDS
    )
    if not args.show_uptime and args.format_key:
        raise ValueError("Cannot use --no-uptime and --format-key together")

    if not args.format_key and args.show_uptime:
        format_key.append(UPTIME)

    finder = Ec2InstanceFinder(use_cache=args.use_cache)
    formatter = Ec2InstanceFormatter(
        format_key=format_key,
        output_format=args.output_format or OUTPUT_PRETTY,
        ip_type=args.ip_type or IP_PRIVATE
    )
    filter = Ec2InstanceFilter(args.pattern)

    return finder, formatter, filter


def main():
    parser = get_argument_parser("find-ec2")
    args = parser.parse_args()

    finder, formatter, filter = create_components(args)
    instances = filter.apply(finder.get_all_instances())

    for instance in instances:
        pretty = formatter.format(instance)
        if pretty:
            print(pretty)


if __name__ == "__main__":
    main()
