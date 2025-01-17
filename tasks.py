from invoke import task, context, Exit
import os
import subprocess
from colorama import *
import glob
from shutil import copy2, rmtree, copytree
from datetime import datetime
import pathlib
from typing import *

from pathlib import Path

init()

DEFAULT_DELPHI_VERSION = "11.1"

g_releases_path = "releases"
g_output = "bin"
g_output_folder = ""  # defined at runtime
g_version = "DEV"

projects = [
    # ("samples\\01_global_logger\\global_logger.dproj", "Win32"),
    # ("samples\\02_file_appender\\file_appender.dproj", "Win32"),
    # ("samples\\03_console_appender\\console_appender.dproj", "Win32"),
    # (
    #     "samples\\04_outputdebugstring_appender\\outputdebugstring_appender.dproj",
    #     "Win32",
    # ),
    # ("samples\\05_vcl_appenders\\vcl_appenders.dproj", "Win32"),
    # ("samples\\08_email_appender\\email_appender.dproj", "Win32"),
    # ("samples\\10_multiple_appenders\\multiple_appenders.dproj", "Win32"),
    # (
    #     "samples\\15_appenders_with_different_log_levels\\multi_appenders_different_loglevels.dproj",
    #     "Win32",
    # ),
    # ("samples\\20_multiple_loggers\\multiple_loggers.dproj", "Win32"),
    # ("samples\\50_custom_appender\\custom_appender.dproj", "Win32"),
    # ("samples\\60_logging_inside_dll\\MainProgram.dproj", "Win32"),
    # ("samples\\60_logging_inside_dll\\mydll.dproj", "Win32"),
    # ("samples\\70_isapi_sample\\loggerproisapisample.dproj", "Win32"),
    # ("samples\\90_remote_logging_with_redis\\REDISAppenderSample.dproj", "Win32"),
    # (
    #     "samples\\90_remote_logging_with_redis\\redis_logs_viewer\\REDISLogsViewer.dproj",
    #     "Win32",
    # ),
    # ("samples\\100_udp_syslog\\udp_syslog.dproj", "Win32"),
    # ("samples\\110_rest_appender\RESTAppenderSample.dproj", "Win32"),
    # ("samples\\110_rest_appender_mobile\RESTAppenderMobileSample.dproj", "Android"),
    # (
    #     "samples\\120_elastic_search_appender\\ElasticSearchAppenderSample.dproj",
    #     "Win32",
    # ),
    ("samples\\rest_logs_collector\RESTLogsCollector.dproj", "Win32"),
]


def get_delphi_projects_to_build(delphi_version=DEFAULT_DELPHI_VERSION):
    global projects
    return projects


def build_delphi_project(
    ctx: context.Context,
    project_filename,
    config="DEBUG",
    delphi_version=DEFAULT_DELPHI_VERSION,
):
    delphi_versions = {
        "10": {"path": "17.0", "desc": "Delphi 10 Seattle"},
        "10.1": {"path": "18.0", "desc": "Delphi 10.1 Berlin"},
        "10.2": {"path": "19.0", "desc": "Delphi 10.2 Tokyo"},
        "10.3": {"path": "20.0", "desc": "Delphi 10.3 Rio"},
        "10.4": {"path": "21.0", "desc": "Delphi 10.4 Sydney"},
        "11": {"path": "22.0", "desc": "Delphi 11 Alexandria"},
        "11.1": {"path": "22.0", "desc": "Delphi 11.1 Alexandria"},
    }

    assert delphi_version in delphi_versions, (
        "Invalid Delphi version: " + delphi_version
    )
    print("[" + delphi_versions[delphi_version]["desc"] + "] ", end="")
    version_path = delphi_versions[delphi_version]["path"]

    rsvars_path = (
        f"C:\\Program Files (x86)\\Embarcadero\\Studio\\{version_path}\\bin\\rsvars.bat"
    )
    if not os.path.isfile(rsvars_path):
        rsvars_path = f"D:\\Program Files (x86)\\Embarcadero\\Studio\\{version_path}\\bin\\rsvars.bat"
        if not os.path.isfile(rsvars_path):
            raise Exception("Cannot find rsvars.bat")
    cmdline = (
        '"'
        + rsvars_path
        + '"'
        + " & msbuild /t:Build /p:Config="
        + config
        + f' /p:Platform={project_filename[1]} "'
        + project_filename[0]
        + '"'
    )
    print("\n" + "".join(cmdline))
    r = ctx.run(cmdline, hide=True, warn=True)
    if r.failed:
        print(r.stdout)
        print(r.stderr)
        raise Exit("Build failed for " + delphi_versions[delphi_version]["desc"])


def zip_samples(version):
    global g_output_folder
    cmdline = (
        "7z a "
        + g_output_folder
        + f"\\..\\{version}_samples.zip -r -i@7ziplistfile.txt"
    )
    return subprocess.call(cmdline, shell=True) == 0


def create_zip(ctx, version):
    global g_output_folder
    print("CREATING ZIP")
    archive_name = version + ".zip"
    switches = ""
    files_name = "*"
    cmdline = f"..\\7z.exe a {switches} {archive_name} *"
    print("cmdline:" + cmdline)
    print("g_output_folder: " + g_output_folder)
    with ctx.cd(g_output_folder):
        ctx.run(cmdline, shell=True)


def copy_sources():
    global g_output_folder
    os.makedirs(g_output_folder + "\\sources", exist_ok=True)
    os.makedirs(g_output_folder + "\\packages", exist_ok=True)
    os.makedirs(g_output_folder + "\\tools", exist_ok=True)
    # copying main sources
    print("Copying LoggerPro Sources...")
    src = glob.glob("*.pas") + glob.glob("*.inc") + glob.glob("*.md")
    for file in src:
        print("Copying " + file + " to " + g_output_folder + "\\sources")
        copy2(file, g_output_folder + "\\sources\\")


def copy_libs(ctx):
    global g_output_folder

    # swagdoc
    print("Copying libraries: SwagDoc...")
    curr_folder = g_output_folder + "\\lib\\swagdoc"
    os.makedirs(curr_folder, exist_ok=True)
    if not ctx.run(rf"xcopy lib\swagdoc\*.* {curr_folder}\*.* /E /Y /R /V /F"):
        raise Exception("Cannot copy SwagDoc")

    # loggerpro
    print("Copying libraries: LoggerPro...")
    curr_folder = g_output_folder + "\\lib\\loggerpro"
    os.makedirs(curr_folder, exist_ok=True)
    if not ctx.run(rf"xcopy lib\loggerpro\*.* {curr_folder}\*.* /E /Y /R /V /F"):
        raise Exception("Cannot copy loggerpro")

    # dmustache
    print("Copying libraries: dmustache...")
    curr_folder = g_output_folder + "\\lib\\dmustache"
    os.makedirs(curr_folder, exist_ok=True)
    if not ctx.run(rf"xcopy lib\dmustache\*.* {curr_folder}\*.* /E /Y /R /V /F"):
        raise Exception("Cannot copy dmustache")


def printkv(key, value):
    print(Fore.RESET + key + ": " + Fore.GREEN + value.rjust(60) + Fore.RESET)


def init_build(version):
    """Required by all tasks"""
    global g_version
    global g_output_folder
    global g_releases_path
    g_version = version
    g_output_folder = g_releases_path + "\\" + g_version
    print()
    print(Fore.RESET + Fore.RED + "*" * 80)
    print(Fore.RESET + Fore.RED + " BUILD VERSION: " + g_version + Fore.RESET)
    print(Fore.RESET + Fore.RED + " OUTPUT PATH  : " + g_output_folder + Fore.RESET)
    print(Fore.RESET + Fore.RED + "*" * 80)

    rmtree(g_output_folder, True)
    os.makedirs(g_output_folder, exist_ok=True)
    f = open(g_output_folder + "\\version.txt", "w")
    f.write("VERSION " + g_version + "\n")
    f.write("BUILD DATETIME " + datetime.now().isoformat() + "\n")
    f.close()
    copy2("README.md", g_output_folder)
    copy2("License.txt", g_output_folder)


def build_delphi_project_list(
    ctx, projects, config="DEBUG", delphi_version=DEFAULT_DELPHI_VERSION
):
    ret = True
    for delphi_project in projects:
        msg = f"Building: {os.path.basename(delphi_project[0])}  ({config})"
        print(Fore.RESET + msg.ljust(90, "."), end="")
        try:
            build_delphi_project(ctx, delphi_project, "DEBUG", delphi_version)
            print(Fore.GREEN + "OK" + Fore.RESET)
        except Exception as e:
            ret = False
            print(Fore.RED + "\n\nBUILD ERROR")
            print(Fore.RESET)
            print(e)
            raise

        # if res.ok:
        #     print(Fore.GREEN + "OK" + Fore.RESET)
        # else:
        #     ret = False
        #     print(Fore.RED + "\n\nBUILD ERROR")
        #     print(Fore.RESET + res.stdout)
        #     print("\n")

    return ret


@task
def clean(ctx, folder=None):
    global g_output_folder
    import os
    import glob

    if folder is None:
        folder = g_output_folder
    print(f"Cleaning folder {folder}")
    output = pathlib.Path(folder)
    to_delete = []
    to_delete += glob.glob(folder + r"\**\*.exe", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.dcu", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.stat", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.res", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.map", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.~*", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.rsm", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.drc", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.log", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.local", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.gitignore", recursive=True)
    to_delete += glob.glob(folder + r"\**\*.gitattributes", recursive=True)

    for f in to_delete:
        print(f"Deleting {f}")
        os.remove(f)

    rmtree(folder + r"\lib\loggerpro\Win32", True)
    rmtree(folder + r"\lib\loggerpro\packages\d100\__history", True)
    rmtree(folder + r"\lib\loggerpro\packages\d100\Win32\Debug", True)
    rmtree(folder + r"\lib\loggerpro\packages\d101\__history", True)
    rmtree(folder + r"\lib\loggerpro\packages\d101\Win32\Debug", True)
    rmtree(folder + r"\lib\loggerpro\packages\d102\__history", True)
    rmtree(folder + r"\lib\loggerpro\packages\d102\Win32\Debug", True)
    rmtree(folder + r"\lib\loggerpro\packages\d103\__history", True)
    rmtree(folder + r"\lib\loggerpro\packages\d103\Win32\Debug", True)
    rmtree(folder + r"\lib\loggerpro\packages\d104\__history", True)
    rmtree(folder + r"\lib\loggerpro\packages\d104\Win32\Debug", True)
    rmtree(folder + r"\lib\dmustache\.git", True)
    rmtree(folder + r"\lib\swagdoc\lib", True)
    rmtree(folder + r"\lib\swagdoc\deploy", True)
    rmtree(folder + r"\lib\swagdoc\demos", True)


@task()
def tests(ctx, delphi_version=DEFAULT_DELPHI_VERSION):
    """Builds and execute the unit tests"""
    import os

    apppath = os.path.dirname(os.path.realpath(__file__))
    res = True
    testclient = r"unittests\UnitTests.dproj"

    print("\nBuilding Unit Tests")
    build_delphi_project(
        ctx, (testclient, "Win32"), config="CI", delphi_version=delphi_version
    )

    import subprocess

    print("\nExecuting tests...")
    r = subprocess.run([r"unittests\Win32\CI\UnitTests.exe"])
    if r.returncode != 0:
        return Exit("Compilation failed: \n" + str(r.stdout))
    if r.returncode > 0:
        print(r)
        print("Unit Tests Failed")
        return Exit("Unit tests failed")


@task(post=[tests])
def build(ctx, version="DEBUG", delphi_version=DEFAULT_DELPHI_VERSION):
    """Builds LoggerPro"""
    init_build(version)
    delphi_projects = get_delphi_projects_to_build(delphi_version)
    ret = build_delphi_project_list(ctx, delphi_projects, version, delphi_version)
    if not ret:
        raise Exit("Build failed")


@task(pre=[tests, build])
def release(
    ctx, version="DEBUG", delphi_version=DEFAULT_DELPHI_VERSION, skip_build=False
):
    """Builds all the projects, executes unit/integration tests and create release"""
    print(Fore.RESET)
    copy_sources()
    # copy_libs(ctx)
    clean(ctx)
    # zip_samples(version)
    create_zip(ctx, version)
