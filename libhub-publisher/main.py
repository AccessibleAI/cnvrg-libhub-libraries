import json
import yaml

from packaging.version import parse as parse_version

from cnvrgv2 import Cnvrg, FlowVersion
from cnvrgv2.errors import CnvrgHttpError

cnvrg = Cnvrg()
flow_version = FlowVersion()

TASK_TYPES = {
    0: "data",
    2: "exec",
    3: "deploy"
}


# Helper functions
def check_if_can_upload(enforce_library_version=False):
    """
    Validates that the blueprint and its libraries are fit to be uploaded to Libhub
    @param enforce_library_version: [Boolean] Throw exception if we are trying to upload a library with lower version
    @return: None
    """

    tasks = flow_version.dag["tasks"]

    # Check if we can upload the libraries
    for task in tasks:
        # We want to make sure that the flow consist only from library tasks without external dependencies
        if not task["project_library"] and not task["libhub_library"]:
            raise Exception("Can't publish a flow with non-library tasks")
        if task["libhub_library"]:
            continue

        library_slug = task["title"].replace(" ", "-").lower()
        try:
            latest_version = cnvrg.libraries.get(library_slug).versions.latest.version
            if parse_version(task["library_version"]) <= parse_version(latest_version) and enforce_library_version:
                raise Exception("Trying to upload a library with a version lower than the latest.")
        except CnvrgHttpError:
            # The library or the latest version does not exist, we can proceed
            pass

    # Check if we can upload the blueprint
    blueprint_slug = flow_version.flow_title.replace(" ", "-").lower()
    try:
        latest_version = cnvrg.blueprints.get(blueprint_slug).versions.latest.version
        if parse_version(flow_version.blueprint_version) <= parse_version(latest_version):
            raise Exception("Trying to upload a blueprint with a version lower than the latest.")
    except CnvrgHttpError:
        # The library or the latest version does not exist, we can proceed
        pass


def create_library_json(library_info):
    """
    Creates the library JSON/YAML representation from the task data
    :param library_info: [Dict] The task information from the flow version
    :return: [Dict] The relevant library information
    """

    library_yaml = {
        "icon": library_info["icon"] or "python",
        "title": library_info["title"],
        "version": library_info["library_version"],
        "description": library_info["library_description"],
        "tags": library_info["library_tags"],
        "author": cnvrg._organization,
        "author_email": cnvrg.me().email,
        "language": "python3",

        "image": library_info["library_image"],
        "requirements": library_info["library_reqs"]
    }

    if library_info.get("cmd"):
        library_yaml["command"] = library_info["cmd"]
        library_yaml["objective"] = library_info["objective"]
        library_yaml["objective_goal"] = library_info["objective_goal"]
        library_yaml["objective_function"] = library_info["objective_function"]
        library_yaml["max_jobs"] = library_info["max_jobs"]
        library_yaml["parallel_jobs"] = library_info["parallel_jobs"]
        library_yaml["algorithm"] = library_info["algorithm"]
        library_yaml["arguments"] = library_info["tags"]
    elif library_info.get("endpoint_slug"):
        library_yaml["kind"] = library_info["kind"]
        library_yaml["arguments"] = {
            "accept_files": False,  # TODO: remove this or add support
            "input_schema": library_info["input_schema"],
            "output_schema": library_info["output_schema"],
            "file_name": library_info["file_name"],
            "function_name": library_info["function_name"],
            "prep_file": library_info["prep_file"],
            "prep_function": library_info["prep_function"],
            "flask_config": library_info["flask_config"],
            "gunicorn_config": library_info["gunicorn_config"],
        }

    # convert all ordered dicts to regular ones and return
    return json.loads(json.dumps(library_yaml))


def find_or_create_library(name):
    """
    Creates a library or retrieves it if its already exist
    @param name: The name (sluggified) of the library
    @return: [Library] The library object
    """

    try:
        print("Creating library {}".format(name))
        return cnvrg.libraries.create(name, public=True)
    except CnvrgHttpError as e:
        if "already exists" not in str(e):
            raise e
        print("Library {} already exists".format(name))
        return cnvrg.libraries.get(name)


def create_library_version(library, schema, folder, auto_bump):
    """
    Creates a library version in libhub
    :param library: [Library] The library object
    :param schema: [Dict] The library yaml schema
    :param folder: [String] The absolute location of the library folder inside the pod
    :param auto_bump: [Boolean] Wether we want to auto bump the library version
    :return: [LibraryVersion] The newly created library version object
    """

    print("Creating library version for {} (auto bump is {})".format(library.name, auto_bump))
    with open("{}/library.yaml".format(folder), 'w') as f:
        f.write(yaml.dump(schema))

    return library.versions.create_version(folder, auto_bump=auto_bump)


def find_or_create_blueprint(name):
    """
    Creates a blueprint or retrieves it if its already exist
    @param name: The name (sluggified) of the library
    @return: [Blueprint] The blueprint object
    """

    try:
        print("Creating blueprint {}".format(name))
        return cnvrg.blueprints.create(name, public=True)
    except CnvrgHttpError as e:
        if "already exists" not in str(e):
            raise e
        print("Blueprint {} already exists".format(name))
        return cnvrg.blueprints.get(name)


def create_blueprint_version(blueprint, schema):
    """
    Creates a blueprint version inside libhub
    :param blueprint: [Blueprint] The blueprint object
    :param schema: [Dict] The blueprint yaml schema
    :return: [BlueprintVersion] The newly created blueprint version object
    """

    print("Creating blueprint version for {}".format(blueprint.name))
    return blueprint.versions.create_version(schema)


def prepare_libraries():
    """
    Creates and uploads libraries from flow version tasks and constructs blueprint task list
    :return: [List] List of blueprint tasks
    """

    print("========================================")

    tasks = flow_version.dag["tasks"]
    libraries = {}
    blueprint_tasks = []
    for task in tasks:
        library_yaml = create_library_json(task)
        libraries[task["library_project_folder"]] = {
            "schema": library_yaml,
            "auto_bump": task["library_version_auto_bump"]
        }

        # Prepare the task fields for the blueprint yaml
        blueprint_task = {**library_yaml}
        blueprint_task["library"] = blueprint_task["title"].replace(" ", "-").lower()
        blueprint_task["library_version"] = blueprint_task.pop("version")
        if blueprint_task.get("command"):
            blueprint_task["params"] = blueprint_task.pop("arguments")
        elif blueprint_task.get("kind"):
            blueprint_task = {**blueprint_task, **blueprint_task["arguments"]}
            blueprint_task.pop("arguments")

        blueprint_tasks.append({
            "top": task["top"],
            "left": task["left"],
            "type": TASK_TYPES[task["type"]],
            **blueprint_task
        })

    # Create and upload libraries
    for folder in libraries:
        abs_folder = "/cnvrg/{}".format(folder)
        auto_bump = libraries[folder]["auto_bump"]
        schema_json = libraries[folder]["schema"]
        library_name = schema_json["title"].replace(" ", "-").lower()

        library = find_or_create_library(library_name)
        library_version = create_library_version(library, schema_json, abs_folder, auto_bump)

        print("Uploading tar file for {} created".format(library.name))
        library_version.upload(abs_folder)

        print("========================================")

    return blueprint_tasks


def prepare_blueprint(tasks):
    """
    Creates the blueprint and blueprint version in libhub
    :param tasks: [List] The blueprint task list
    :return: None
    """

    blueprint_name = flow_version.flow_title.replace(" ", "-").lower()

    # Prepare dict to map relation slugs to titles
    task_uid_to_title = {}
    for task in flow_version.dag["tasks"]:
        task_uid_to_title[task["uid"]] = task["title"]

    # Create relations
    relations = []
    for relation in flow_version.dag["relations"]:
        relations.append({
            "to": task_uid_to_title[relation["to"]],
            "from": task_uid_to_title[relation["from"]],
        })

    blueprint_schema = {
        "title": flow_version.flow_title,
        "version": flow_version.blueprint_version,
        "description": flow_version.blueprint_summary,
        "long_description": flow_version.blueprint_description,
        "tags": flow_version.blueprint_tags,
        "author": cnvrg._organization,
        "author_email": cnvrg.me().email,
        "tasks": tasks,
        "relations": relations
    }

    blueprint = find_or_create_blueprint(blueprint_name)
    create_blueprint_version(blueprint, blueprint_schema)


if __name__ == "__main__":
    # Check if its possible to upload the blueprint and the libraries
    check_if_can_upload()

    # Collect and upload libraries
    blueprint_tasks = prepare_libraries()

    # Collect and upload blueprint
    prepare_blueprint(blueprint_tasks)
