import os.path
import os
from shutil import copytree, copy2, rmtree
import tempfile

from flask import current_app


class PuzzleResource():
    def __init__(self, puzzle_id, config):
        self.puzzle_id = puzzle_id
        self.config = config
        self.target_dir = None
        self._temp_dir = None
        self.is_local_resource = True
        if self.is_local_resource:
            self.target_dir = os.path.join(
                self.config["PUZZLE_RESOURCES"],
                self.puzzle_id
            )
            os.makedirs(self.target_dir, exist_ok=True)

    def __del__(self):
        if self._temp_dir is not None:
            current_app.logger.debug(f"Cleaning up temp puzzle resource for {self.puzzle_id} located at {self._temp_dir}")
            # TODO: delete the temp dir

    def put(self, src_dir):
        """
        copy all content in src_dir to the puzzle resource location.
        """
        if self.is_local_resource:
            assert self.target_dir is not None
            copytree(src_dir, self.target_dir, dirs_exist_ok=True)
            return

        # TODO: upload to remote location (S3 bucket)

    def put_file(self, file_path):
        if self.is_local_resource:
            copy2(file_path, self.target_dir)

    def yank(self):
        """
        mk temp directory
        populate with puzzle resources
        """
        if self.is_local_resource:
            # No need to fetch puzzle resources since it is local.
            return self.target_dir

        self.target_dir = self._temp_dir = tempfile.mkdtemp()
        # TODO: download resource files from remote location if available
        return self.target_dir

    def yank_file(self, file_path):
        if self.is_local_resource:
            return os.path.join(self.target_dir, file_path)

    def purge(self):
        if self.is_local_resource:
            if not os.path.exists(self.target_dir):
                return
            rmtree(self.target_dir)
            return

        # TODO: delete all remote puzzle resource files

    def delete(self):
        ""
        os.rmdir(self.target_dir)
