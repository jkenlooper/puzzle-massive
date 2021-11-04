import os.path
import os
from shutil import copytree, copy2, rmtree
import tempfile
import re
import mimetypes

from flask import current_app
import botocore
import boto3


def is_puzzle_resource_file_private(file_path):
    """
    The original.jpg and original.uuid-slip.jpg files should not be public.
    """
    return re.match(r"original.([^.]+\.)?jpg", os.path.basename(file_path)) is not None


class PuzzleResource:
    def __init__(self, puzzle_id, config, is_local_resource=True):
        self.puzzle_id = puzzle_id
        self.config = config
        self.target_dir = None
        self._temp_dir = None
        self.is_local_resource = is_local_resource
        if self.is_local_resource:
            self.target_dir = os.path.join(
                self.config["PUZZLE_RESOURCES"], self.puzzle_id
            )
            os.makedirs(self.target_dir, exist_ok=True)
        else:
            current_app.logger.debug(
                self.config["PUZZLE_RESOURCES_BUCKET_ENDPOINT_URL"]
            )
            self.s3 = boto3.client(
                "s3", endpoint_url=self.config["PUZZLE_RESOURCES_BUCKET_ENDPOINT_URL"]
            )
            self._temp_dir = tempfile.mkdtemp()
            self.target_dir = os.path.join(self._temp_dir, self.puzzle_id)
            os.mkdir(self.target_dir)

    def __del__(self):
        if self._temp_dir is not None:
            debug_msg = f"Cleaning up temp puzzle resource for {self.puzzle_id} located at {self._temp_dir}"
            try:
                current_app.logger.debug(debug_msg)
            except RuntimeError as err:
                # current_app may not be available at this point.
                print(err)
                print(debug_msg)
            rmtree(self._temp_dir)

    def put(self, src_dir):
        """
        copy all content in src_dir to the puzzle resource location.
        """
        if self.is_local_resource:
            assert self.target_dir is not None
            copytree(src_dir, self.target_dir, dirs_exist_ok=True)
            return

        file_paths = []
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                file_paths.append(os.path.join(root, file))
        for file_path in file_paths:
            self.put_file(file_path, dirs=os.path.dirname(file_path[len(src_dir) :]))

    def put_file(self, file_path, dirs=""):
        if self.is_local_resource:
            local_dir = os.path.join(self.target_dir, dirs)
            os.makedirs(local_dir, exist_ok=True)
            # Any existing file should be considered to be immutable and will
            # NOT be replaced.
            if os.path.exists(os.path.join(local_dir, os.path.basename(file_path))):
                current_app.logger.warning(
                    f"Skipping replacement of existing immutable file path: {os.path.join(local_dir, os.path.basename(file_path))}"
                )
                # os.remove(os.path.join(local_dir, os.path.basename(file_path)))
            else:
                copy2(file_path, local_dir)
            return

        PUZZLE_RESOURCES_BUCKET = self.config["PUZZLE_RESOURCES_BUCKET"]
        private = is_puzzle_resource_file_private(file_path)
        if dirs.startswith("/"):
            dirs = dirs[1:]
        path = os.path.join(dirs, os.path.basename(file_path))

        try:
            self.s3.head_object(
                Bucket=PUZZLE_RESOURCES_BUCKET,
                Key=f"resources/{self.puzzle_id}/{path}",
            )
        except botocore.exceptions.ClientError as err:
            # This key shouldn't already exist.
            if err.response["Error"]["Code"] == "404":
                pass
            else:
                current_app.logger.error(err.response)
                current_app.logger.error(
                    f"The object at resources/{self.puzzle_id}/{path} already exists."
                )
                raise Exception(
                    f"Immutable object conflict: resources/{self.puzzle_id}/{path} has already been added to the {PUZZLE_RESOURCES_BUCKET} s3 bucket"
                )

        with open(file_path, "rb") as file:
            self.s3.put_object(
                ACL="private" if private else "public-read",
                Body=file,
                Bucket=PUZZLE_RESOURCES_BUCKET,
                Key=f"resources/{self.puzzle_id}/{path}",
                ContentType=mimetypes.guess_type(path)[0],
                CacheControl=self.config[
                    "PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL"
                ],
                Metadata={
                    # The owner is used to prevent other environments from deleting
                    # this object if it is shared.
                    "owner": self.config["DOMAIN_NAME"]
                },
            )

    def copy_file(self, pr_src, path):
        if path.startswith("/"):
            path = path[1:]
        if self.is_local_resource:
            file_path = os.path.join(pr_src.target_dir, path)
            target_dir_for_path = os.path.join(self.target_dir, path)
            os.makedirs(os.path.dirname(target_dir_for_path), exist_ok=True)
            copy2(file_path, target_dir_for_path)
            return

        PUZZLE_RESOURCES_BUCKET = self.config["PUZZLE_RESOURCES_BUCKET"]
        private = is_puzzle_resource_file_private(path)
        self.s3.copy_object(
            ACL="private" if private else "public-read",
            CopySource={
                "Bucket": PUZZLE_RESOURCES_BUCKET,
                "Key": f"resources/{pr_src.puzzle_id}/{path}",
            },
            Bucket=PUZZLE_RESOURCES_BUCKET,
            Key=f"resources/{self.puzzle_id}/{path}",
            ContentType=mimetypes.guess_type(path)[0],
            CacheControl=self.config["PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL"],
            Metadata={
                # The owner is used to prevent other environments from deleting
                # or modifying this object if it is shared.
                "owner": self.config["DOMAIN_NAME"]
            },
        )

    def list(self):
        if self.is_local_resource:
            # No need to fetch puzzle resources since it is local.
            paths = []
            for root, dirs, files in os.walk(self.target_dir):
                for file in files:
                    paths.append(os.path.join(root[len(self.target_dir) :], file))
            return paths

        PUZZLE_RESOURCES_BUCKET = self.config["PUZZLE_RESOURCES_BUCKET"]
        response = self.s3.list_objects_v2(
            Bucket=PUZZLE_RESOURCES_BUCKET,
            Prefix=f"resources/{self.puzzle_id}/",
        )
        if response["IsTruncated"]:
            raise Exception(
                f"Remote PuzzleResource is not configured to handle truncated responses when listing files at resources/{self.puzzle_id}/"
            )

        paths = list(
            map(
                lambda x: x["Key"][len(f"resources/{self.puzzle_id}/") :],
                response["Contents"],
            )
        )
        return paths

    def yank_file(self, file_path):
        if self.is_local_resource:
            return os.path.join(self.target_dir, file_path)

        PUZZLE_RESOURCES_BUCKET = self.config["PUZZLE_RESOURCES_BUCKET"]
        # Need to verify that the file exists before downloading it.
        try:
            self.s3.head_object(
                Bucket=PUZZLE_RESOURCES_BUCKET,
                Key=f"resources/{self.puzzle_id}/{file_path}",
            )
        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "404":
                raise Exception(
                    f"No file found at: {PUZZLE_RESOURCES_BUCKET} resources/{self.puzzle_id}/{file_path}"
                )
            else:
                raise err
        else:
            tmp_file_dir = os.path.dirname(os.path.join(self.target_dir, file_path))
            os.makedirs(tmp_file_dir, exist_ok=True)

            with open(
                os.path.join(tmp_file_dir, os.path.basename(file_path)), "wb"
            ) as file:
                self.s3.download_fileobj(
                    Bucket=PUZZLE_RESOURCES_BUCKET,
                    Key=f"resources/{self.puzzle_id}/{file_path}",
                    Fileobj=file,
                )
        return os.path.join(self.target_dir, file_path)

    def purge_file(self, file_path):
        if self.is_local_resource:
            if not os.path.exists(os.path.join(self.target_dir, file_path)):
                return
            os.remove(os.path.join(self.target_dir, file_path))
            return

        PUZZLE_RESOURCES_BUCKET = self.config["PUZZLE_RESOURCES_BUCKET"]

        try:
            response = self.s3.head_object(
                Bucket=PUZZLE_RESOURCES_BUCKET,
                Key=f"resources/{self.puzzle_id}/{file_path}",
            )
        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "404":
                return
            else:
                raise err

        # Skip deleting objects that are not owned by this domain.
        if response["Metadata"]["owner"] != self.config["DOMAIN_NAME"]:
            return

        self.s3.delete_objects(
            Bucket=PUZZLE_RESOURCES_BUCKET,
            Delete={
                "Objects": [{"Key": f"resources/{self.puzzle_id}/{file_path}"}],
                "Quiet": True,
            },
        )

    def purge(self, exclude_regex=None):
        if self.is_local_resource:
            if not os.path.exists(self.target_dir):
                return

            if exclude_regex is not None:
                for root, dirs, files in os.walk(self.target_dir):
                    for file in files:
                        if re.search(exclude_regex, file) is None:
                            os.remove(os.path.join(root, file))
            else:
                rmtree(self.target_dir, ignore_errors=True)
            return

        PUZZLE_RESOURCES_BUCKET = self.config["PUZZLE_RESOURCES_BUCKET"]

        try:
            paths = self.list()
        except Exception as err:
            current_app.logger.warning(f"Ignoring error from puzzle_resource.py purge() with puzzle_id {self.puzzle_id} : {err}")
            paths = []
        paths_to_delete = []

        for path in paths:
            try:
                response = self.s3.head_object(
                    Bucket=PUZZLE_RESOURCES_BUCKET,
                    Key=f"resources/{self.puzzle_id}/{path}",
                )
            except botocore.exceptions.ClientError as err:
                if err.response["Error"]["Code"] == "404":
                    continue
                else:
                    raise err

            # Skip deleting objects that are not owned by this domain.
            if response["Metadata"]["owner"] != self.config["DOMAIN_NAME"]:
                continue

            if exclude_regex is not None:
                if re.search(exclude_regex, os.path.basename(path)) is not None:
                    continue

            paths_to_delete.append(path)

        if len(paths_to_delete) > 0:
            self.s3.delete_objects(
                Bucket=PUZZLE_RESOURCES_BUCKET,
                Delete={
                    "Objects": list(
                        map(
                            lambda x: {"Key": f"resources/{self.puzzle_id}/{x}"},
                            paths_to_delete,
                        )
                    ),
                    "Quiet": True,
                },
            )

    def delete(self):
        ""
        os.rmdir(self.target_dir)
