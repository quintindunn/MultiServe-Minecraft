from config import JAVA_JDK8, JAVA_JDK16, JAVA_JDK17

import os
import re
import stat
import subprocess
import time
from datetime import datetime

from pathlib import Path

import shutil
import os.path
import requests

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / Path("log/")

CURRENT_DIR = BASE_DIR / Path("client_servers/current/")
PREVIOUS_DIR = BASE_DIR / Path("client_servers/previous/")

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


# TODO: Add automatic method.
def java_version(version):
    """
    Returns the path to the java executable for a given minecraft version
    :param version: Minecraft Version
    :return: Path to java executable for minecraft version
    """
    version = version.split(".")
    version_core = version[1]
    if int(version_core) < 17 or (len(version) == 2 and version_core == "17"):
        return JAVA_JDK8
    elif int(version_core) == 17 and version[2] == "1":
        return JAVA_JDK16
    return JAVA_JDK17


def get_file_name(file_format: str = FILE_FORMATTING, version: str = "LATEST") -> str:
    """
    Generate the file/folder name based off parameters in the string
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
    """
    Gets list of minecraft versions with the url to their json data
    :return: Dict of version, url pairs.
    """
    url = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"

    request = requests.get(url)
    data = request.json()
    game_versions = {x['id']: x['url'] for x in data['versions']}
    game_versions['LATEST'] = game_versions[data['latest']['release']]

    return game_versions


def get_server_jar(server_type: str = "VANILLA", url: [str, None] = None) -> bytes:
    """
    Get server jar file's contents
    :param server_type: Type of server e.g. "VANILLA", "SPIGOT"
    :param url: URL to jar file to download (For vanilla only)
    :return: Byte data of jar file.
    """
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
    """
    Create new server for a given version
    :param new_version: Minecraft version to change to
    :param server_type: Type of server e.g. "VANILLA", "SPIGOT"
    :param kwargs:
    :return: None
    """
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

    create_server_base(version=server_type + new_version, server_path=CURRENT_DIR)
    methods = {
        "VANILLA": create_vanilla_server,
        "SPIGOT": create_spigot_server
    }
    methods[server_type.upper()](version=new_version, **kwargs)


def create_server_base(version: str, server_path: [str, Path]) -> None:
    """
    Create `version.txt` containing the version of the minecraft server for archiving
    :param version: Minecraft version
    :param server_path: Path to server files
    :return: None
    """
    if not isinstance(server_path, Path):
        server_path = Path(server_path)

    with open(server_path / "version.txt", 'w') as f:
        f.write(version)


def create_vanilla_server(version: str, eula: bool = True, ram: str = "1024", server_name: str = "server.jar") -> None:
    """
    Create a minecraft vanilla server
    :param version: Minecraft Server Version
    :param eula: Agree to eula
    :param ram: How much ram to give server (M)
    :param server_name: Name of server jar
    :return: None
    """
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


def build_buildtools(path: [str, Path], version: str) -> None:
    """
    Builds buildtools for a given version
    :param path: Path to buildtools folder
    :param version: Minecraft version
    :return: None
    """
    start_dir = os.getcwd()
    try:
        if not isinstance(path, Path):
            path = Path(path)

        BUILD_TOOLS_DIR = path / "tmp"
        os.makedirs(BUILD_TOOLS_DIR, exist_ok=True)
        buildtools_bytes = get_server_jar(server_type="SPIGOT")
        with open(BUILD_TOOLS_DIR / "buildtools.jar", 'wb') as f:
            f.write(buildtools_bytes)

        os.chdir(BUILD_TOOLS_DIR)
        command = f"{java_version(version) / 'java.exe'} -Xmx512M -jar buildtools.jar --rev {version}".split()

        with open(CURRENT_DIR / "build_stdout.txt", 'w+') as f, open(CURRENT_DIR / "build_stderr.txt", 'w+') as e:
            proc = subprocess.Popen(command, stdout=f, stderr=e)
            proc.wait(timeout=1200)
    except Exception as e:
        raise e
    finally:
        os.chdir(start_dir)


def create_spigot_server(version: str, eula: bool = True, ram: str = "1024", server_name: str = "server.jar") -> None:
    """
    Create a spigot server for a given version
    :param version: Minecraft Server Version
    :param eula: Agree to eula
    :param ram: How much ram to give server (M)
    :param server_name: Name of server jar
    :return: None
    """
    start_dir = os.getcwd()
    build_buildtools(CURRENT_DIR, version)
    os.chdir(start_dir)
    server_name = server_name + ".jar" if not server_name.endswith(".jar") else server_name
    r = re.compile("spigot-.*.jar")
    matches = list(filter(r.match, os.listdir(CURRENT_DIR / "tmp/")))
    shutil.move(CURRENT_DIR / "tmp" / matches[0], CURRENT_DIR / server_name)

    os.makedirs(LOG_DIR / "builds", exist_ok=True)

    shutil.move(CURRENT_DIR / "build_stdout.txt", LOG_DIR / 'builds' / f"{time.time_ns()}_build_stdout.txt")
    shutil.move(CURRENT_DIR / "build_stderr.txt", LOG_DIR / 'builds' / f"{time.time_ns()}_build_stderr.txt")

    # TODO: Fix removing of CURRENT_DIR/tmp
    shutil.rmtree(CURRENT_DIR / "tmp/", ignore_errors=True)

    if eula:
        with open(CURRENT_DIR / "eula.txt", 'w') as f:
            f.write("eula=True")

    with open(CURRENT_DIR / "run.bat", 'w') as f:
        f.write(f"""@echo off
        java -Xmx{ram}M -Xms{ram}M -jar {server_name} nogui""")


if __name__ == '__main__':
    update_current_version('1.18.2', server_type="SPIGOT")



