import json
import os

# read config.json

with open('./config.json') as f:
    config = json.load(f)

qa_repo = config["global"]["qaRepo"]
release_repo = config["global"]["releaseRepo"]
image_version = config["global"]["imageVersion"]
chrome_base_image = config["global"]["chromeBaseImage"]
firefox_base_image = config["global"]["firefoxBaseImage"]
releaseBrowser = config["global"]["releaseBrowser"]
releaseOn = config["global"]["releaseOn"]

path = ""
if config["global"]["browserDockerFilePath"]:
    path = "cd " + config["global"]["browserDockerFilePath"] + " && "

if config["global"]["executeWithSudo"]:
    docker_command = path + "sudo docker "
else:
    docker_command = path + "docker "

# clean older log file
open("releaseCompletion.log", 'w').close()


print("")
print("---------------- Config Parameters ------------------")

print("qa_repo : " + qa_repo)
print("release_repo : " + release_repo)
print("image_version : " + image_version)
print("chrome_base_image : " + chrome_base_image)
print("firefox_base_image : " + firefox_base_image)

print("----------------------- END --------------------------")
print("\n\n")


def execute_shell_command(command):
    print("Executing : " + command)
    if not config["global"]["onlyDebug"]:
        return os.system(command)

def fetch_image_id(name):
    return "$(" + docker_command + "images " + name + ":" + image_version + " --format {{.ID}})"

def docker_push(release_name, name):

    if release_name == "release":
        repo = release_repo
    if release_name == "qa":
        repo = qa_repo

    execute_shell_command(docker_command + "login " + repo + " --username=$DOCKER_USER --password=$DOCKER_PASS")

    # Artifactory path
    artifactory_path = repo + "/" + name + ":" + image_version

    # Attach TAG
    execute_shell_command(docker_command + "tag " + fetch_image_id(name) + " " + artifactory_path)

    # Push image
    execute_shell_command(docker_command + "push " + artifactory_path)


def generate_build_command(name, version, base):

    if base == "chrome":
        image_base = chrome_base_image
    if base == "firefox":
        image_base = firefox_base_image

    return docker_command + "build -t " + name + ":" + image_version + " --build-arg BASE_IMAGE=" \
           + image_base + ":" + version + " . --no-cache"


release_data = ["release", "qa"]
browser_data = ["chrome", "firefox"]

for browser in browser_data:
    if releaseBrowser == browser or releaseBrowser == "all":
        for browser_list in config[browser]:
            name = browser_list["imageName"]
            version = browser_list["baseVersion"]

            execute_shell_command(generate_build_command(name, version, browser))

            for rel in release_data:
                if releaseOn == rel or releaseOn == "all":
                    docker_push(rel, name)
                    print("-------------" + name + " :  Image Pushed ------------")
                    
                    releaseLog = open("releaseCompletion.log", "a+")
                    releaseLog.write("Browser : " + name + " , Repo : " + rel + "\n")
                    releaseLog.close() 


            # Clean docker images
            execute_shell_command(docker_command + " system prune --all --force")

