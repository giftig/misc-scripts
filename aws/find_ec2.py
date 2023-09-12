#!/usr/bin/python3

import argparse
import datetime
import json
import math
import os
from typing import Optional

import boto3

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
        help="Exclude instance uptime from display"
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

    def __str__(self):
        return f"{self.name}\t{self.private_ip}\t{self.instance_id}"

    def __gt__(self, other):
        my_key = [self.name or "", self.private_ip or "", self.instance_id]
        other_key = [
            other.name or "", other.private_ip or "", other.instance_id
        ]

        return my_key > other_key


class Ec2InstanceFormatter:
    def __init__(self, ip_type=IP_PRIVATE, show_uptime=True):
        self.ip_type = ip_type
        self.show_uptime = show_uptime

    def format_uptime(self, instance):
        now = datetime.datetime.utcnow()
        launch_time = instance.launch_time.replace(tzinfo=None)

        uptime = (now - launch_time).total_seconds()
        units = "s"

        if uptime > 60:
            uptime /= 60
            units = "m"

        if uptime > 60:
            uptime /= 60
            units = "h"

        if uptime > 24:
            uptime /= 24
            units = "d"

        pretty_uptime = f"{math.floor(uptime)}{units}"
        pretty_state = STATE_ICONS[instance.state_code]

        return f"{pretty_state} {pretty_uptime}"

    def format_line(self, instance, ip):
        """
        One line of output format, specifying an IP to display. Where an
        instance has multiple IPs associated and we want to see all of them,
        such as with --alt-ip, we will emit multiple records, one for each IP
        """
        name = instance.name or "(no name)"
        ip = ip or ""
        instance_id = instance.instance_id
        uptime = self.format_uptime(instance)

        line = (
            f"{name : <34} "
            f"{ip : <16} "
            f"{instance_id : <21}"
        )

        if self.show_uptime:
            line += f"{uptime : <7}"

        return line

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
        self.ec2 = boto3.client("ec2")
        self.session = boto3.Session()
        self.use_cache = use_cache

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


def main():
    parser = get_argument_parser("find-ec2")
    args = parser.parse_args()

    finder = Ec2InstanceFinder(use_cache=args.use_cache)
    formatter = Ec2InstanceFormatter(
        ip_type=args.ip_type or IP_PRIVATE,
        show_uptime=args.show_uptime
    )
    filter = Ec2InstanceFilter(args.pattern)
    instances = filter.apply(finder.get_all_instances())

    for instance in instances:
        pretty = formatter.format(instance)
        if pretty:
            print(pretty)


if __name__ == "__main__":
    main()
