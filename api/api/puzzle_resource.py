import os.path
import os
from shutil import copytree, copy2, rmtree
import tempfile

from flask import current_app

import boto3


class PuzzleResource():
    def __init__(self, puzzle_id, config, is_local_resource=True):
        self.puzzle_id = puzzle_id
        self.config = config
        self.target_dir = None
        self._temp_dir = None
        self.is_local_resource = is_local_resource
        if self.is_local_resource:
            self.target_dir = os.path.join(
                self.config["PUZZLE_RESOURCES"],
                self.puzzle_id
            )
            os.makedirs(self.target_dir, exist_ok=True)
        else:
            current_app.logger.warning("Remote PuzzleResource is not fully implemented.")
            self.s3 = boto3.client('s3', endpoint_url=self.config["PUZZLE_RESOURCES_BUCKET_ENDPOINT_URL"])
            self._temp_dir = tempfile.mkdtemp()
            self.target_dir = os.path.join(self._temp_dir, self.puzzle_id)
            os.mkdir(self.target_dir)

    def __del__(self):
        if self._temp_dir is not None:
            current_app.logger.debug(f"Cleaning up temp puzzle resource for {self.puzzle_id} located at {self._temp_dir}")
            rmtree(self._temp_dir)

    def put(self, src_dir):
        """
        copy all content in src_dir to the puzzle resource location.
        """
        if self.is_local_resource:
            assert self.target_dir is not None
            copytree(src_dir, self.target_dir, dirs_exist_ok=True)
            return

        current_app.logger.warning("Remote PuzzleResource for 'put' is not fully implemented.")
        # TODO: upload to remote location (S3 bucket)

    def put_file(self, file_path, dirs="", private=True):
        if self.is_local_resource:
            local_dir = os.path.join(self.target_dir, dirs)
            os.makedirs(local_dir, exist_ok=True)
            copy2(file_path, local_dir)
            return

        current_app.logger.warning("Remote PuzzleResource for 'put_file' is not fully implemented.")
        # TODO: upload to remote location (S3 bucket)
        PUZZLE_RESOURCES_BUCKET = self.config["PUZZLE_RESOURCES_BUCKET"]
        path = os.path.join(dirs, os.path.basename(file_path))
        self.s3.put_object(
            ACL="private" if private else "public-read",
            Body=file,
            Bucket=PUZZLE_RESOURCES_BUCKET,
            Key=f"{self.puzzle_id}/{path}",
            CacheControl=self.config["PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL"],
            Metadata = {
                # The owner is used to prevent other environments from deleting
                # or modifying this object if it is shared.
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
        self.s3.copy_object(
            CopySource = {
                "Bucket": PUZZLE_RESOURCES_BUCKET,
                "Key": f"{pr_src.puzzle_id}/{path}"
            },
            Bucket=PUZZLE_RESOURCES_BUCKET,
            Key=f"{self.puzzle_id}/{path}",
            CacheControl=self.config["PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL"],
            Metadata = {
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
                    paths.append(os.path.join(root[len(self.target_dir):], file))
            return paths

        current_app.logger.warning("Remote PuzzleResource for 'list' is not fully implemented.")
        # TODO: return listing of remote files
        return []

    def yank_file(self, file_path):
        if self.is_local_resource:
            return os.path.join(self.target_dir, file_path)

        current_app.logger.warning("Remote PuzzleResource for 'yank_file' is not fully implemented.")
        # TODO: download file from remote location and place in target_dir
        return os.path.join(self.target_dir, file_path)

    def purge(self):
        if self.is_local_resource:
            if not os.path.exists(self.target_dir):
                return
            rmtree(self.target_dir)
            return

        current_app.logger.warning("Remote PuzzleResource for 'purge' is not fully implemented.")
        # TODO: delete all remote puzzle resource files

    def delete(self):
        ""
        os.rmdir(self.target_dir)
