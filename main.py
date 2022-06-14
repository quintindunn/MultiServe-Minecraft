import subprocess
from datetime import datetime

from pathlib import Path

import shutil
import os.path
import requests

BASE_DIR = Path(__file__).resolve().parent

# UTIL_DIR = BASE_DIR / Path("util/")

CURRENT_DIR = BASE_DIR / Path("client_servers/current/")
PREVIOUS_DIR = BASE_DIR / Path("client_servers/previous/")

JAVA_BIN = "C:\\Program Files (x86)\\Java\\jre1.8.0_333\\bin"

"""
Formatting:

%V - Version

%Y - Year
%M - Month
%D - Day

%H - Hour
%m - Minute
%S - Second

"""
FILE_FORMATTING = "%V__%M-%D-%Y__%H-%M-%S"


def get_file_name(file_format: str = FILE_FORMATTING, version: str = "LATEST") -> str:
    """
    Generate the file/folder name based off parameters in the string.
    :param file_format: Formatting for the filename .
    :param version: Minecraft version.
    :return: String of formatted filename.
    """
    current_time = datetime.now()
    # Map key to value
    convert = {
        "%V": version,

        "%Y": str(current_time.year),
        "%M": str(current_time.month),
        "%D": str(current_time.day),

        "%H": str(current_time.hour),
        "%m": str(current_time.minute),
        "%S": str(current_time.second),
    }
    data = file_format
    # The .keys() isn't required, just looks cleaner
    for key, value in zip(convert, convert.values()):
        data = data.replace(key, value)

    return data


def get_vanilla_versions() -> dict:
    url = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"

    request = requests.get(url)
    data = request.json()
    game_versions = {x['id']: x['url'] for x in data['versions']}
    game_versions['LATEST'] = game_versions[data['latest']['release']]

    return game_versions


def get_server_jar(server_type: str = "VANILLA", url: [str, None] = None) -> bytes:
    if server_type == "VANILLA":
        content = requests.get(requests.get(url).json()['downloads']['server']['url']).content
        return content
    elif server_type == "SPIGOT":
        # Get buildtools to build spigot.
        url = "https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar"
        content = requests.get(url).content
        return content

    raise ValueError(f"Unknown server_type: \"{server_type}\"")


def update_current_version(new_version: str = "LATEST", server_type: str = "VANILLA", **kwargs) -> None:
    if not os.path.isdir(PREVIOUS_DIR):
        os.makedirs(PREVIOUS_DIR, exist_ok=True)
    if not os.path.isdir(CURRENT_DIR):
        current = None
        os.makedirs(CURRENT_DIR, exist_ok=True)
    else:
        if os.path.isfile(CURRENT_DIR / "version.txt"):
            with open(CURRENT_DIR / "version.txt", 'r') as f:
                current = f.read()
        else:
            current = ""

    if current:
        previous_directory = os.path.join(PREVIOUS_DIR, get_file_name(FILE_FORMATTING, current))
        shutil.move(CURRENT_DIR, previous_directory)
        os.mkdir(CURRENT_DIR)

    create_server_base(version=new_version, server_path=CURRENT_DIR)
    methods = {
        "VANILLA": create_vanilla_server,
        "SPIGOT": create_spigot_server
    }
    methods[server_type.upper()](version=new_version, **kwargs)


def create_server_base(version: str, server_path: [str, Path]) -> None:
    if not isinstance(server_path, Path):
        server_path = Path(server_path)

    with open(server_path / "version.txt", 'w') as f:
        f.write(version)


def create_vanilla_server(version: str, eula: bool = True, ram: str = "1024", server_name: str = "server.jar") -> None:
    versions = get_vanilla_versions()
    jar_data = get_server_jar(url=versions[version], server_type="VANILLA")
    if not server_name.endswith(".jar"):
        server_name += ".jar"

    create_server_base(version, CURRENT_DIR)
    with open(CURRENT_DIR / server_name, 'wb') as f:
        f.write(jar_data)

    if eula:
        with open(CURRENT_DIR / "eula.txt", 'w') as f:
            f.write("eula=True")

    with open(CURRENT_DIR / "run.bat", 'w') as f:
        f.write(f"""@echo off
        java -Xmx{ram}M -Xms{ram}M -jar {server_name} nogui""")


if __name__ == '__main__':
    update_current_version('1.19', server_type="VANILLA")
