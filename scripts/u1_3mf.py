"""Bounded reads and command checks for untrusted 3MF input; standard library only."""
from pathlib import PurePosixPath, PureWindowsPath
import xml.etree.ElementTree as ET

MAX_SETTINGS_BYTES = 1024**2
MAX_MEMBER_BYTES = 512 * 1024**2
MAX_PROJECT_BYTES = 2 * 1024**3
MAX_MEMBERS = 10000
POST_PROCESS = {"post_process", "post_process_script", "post_process_scripts"}


def validate_archive(archive):
    members = archive.infolist()
    if len(members) > MAX_MEMBERS:
        raise ValueError("3MF exceeds the 10000-member limit")
    names = [item.filename.casefold() for item in members]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate/case-ambiguous 3MF members are unsupported")
    for item in members:
        name = item.orig_filename
        if ("\\" in name or "\x00" in name or name.startswith("/") or PureWindowsPath(name).drive
                or ".." in PurePosixPath(name).parts or item.flag_bits & 1):
            raise ValueError("Unsafe or encrypted 3MF archive member")
        if item.file_size > MAX_MEMBER_BYTES:
            raise ValueError("3MF member exceeds the 512 MiB limit")
    if sum(item.file_size for item in members) > MAX_PROJECT_BYTES:
        raise ValueError("Uncompressed 3MF exceeds the 2 GiB limit")


def read_member(archive, name, limit=MAX_SETTINGS_BYTES):
    member = archive.getinfo(name)
    if member.file_size > limit:
        raise ValueError("3MF member exceeds its read limit")
    with archive.open(member) as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("3MF member exceeds its read limit")
    return data


class _NoDoctype(ET.TreeBuilder):
    def doctype(self, name, pubid, system):
        raise ValueError("XML declarations/entities are unsupported")


def parse_xml(data):
    # A parser callback also catches UTF-16/32 declarations missed by byte regexes.
    return ET.fromstring(data, parser=ET.XMLParser(target=_NoDoctype()))


def reject_post_process(settings):
    if not isinstance(settings, dict):
        raise ValueError("Project settings must be a JSON object")
    for key in POST_PROCESS:
        value = settings.get(key)
        if value is None or isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, list) and all(isinstance(item, str) and not item.strip() for item in value):
            continue
        raise ValueError("Post-processing commands are unsupported; remove them from a reviewed copy in Orca")
