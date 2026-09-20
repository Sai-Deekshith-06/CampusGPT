from pathlib import Path
import shutil

from fastapi import HTTPException

from file_manager.core.config import settings


class FileSystemService:

    @property
    def root(self) -> Path:
        if settings.root is None:
            raise HTTPException(
                status_code=500,
                detail="Filesystem root is not configured.",
            )

        return settings.root

    # ---------------------------------------------------------
    # PATH SECURITY
    # ---------------------------------------------------------

    def safe_path(self, relative_path: str | None) -> Path:
        import os
        if not relative_path:
            relative_path = "/"

        relative_path = relative_path.replace("\\", "/").lstrip("/")

        target = Path(os.path.abspath(self.root / relative_path))

        try:
            target.relative_to(Path(os.path.abspath(self.root)))
        except ValueError:
            raise HTTPException(
                status_code=403,
                detail="Unsafe path.",
            )

        return target

    def validate_name(self, name: str):
        if not name:
            raise HTTPException(
                status_code=400,
                detail="Name cannot be empty.",
            )

        if name in (".", ".."):
            raise HTTPException(
                status_code=400,
                detail="Invalid name.",
            )

        if "/" in name or "\\" in name:
            raise HTTPException(
                status_code=400,
                detail="Invalid name.",
            )

    # ---------------------------------------------------------
    # FILE INFORMATION
    # ---------------------------------------------------------

    def get_metadata_path(self, path: Path) -> Path:
        return path.parent / f".{path.name}.meta.json"

    def read_metadata(self, path: Path) -> dict:
        meta_path = self.get_metadata_path(path)
        if meta_path.exists():
            import json
            try:
                with meta_path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def write_metadata(self, path: Path, metadata: dict):
        meta_path = self.get_metadata_path(path)
        import json
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f)

    def delete_metadata(self, path: Path):
        meta_path = self.get_metadata_path(path)
        if meta_path.exists():
            meta_path.unlink()

    def to_path(self, path: Path) -> dict:
        stat = path.stat()

        relative = path.relative_to(self.root)

        if str(relative) == ".":
            relative_path = "/"
        else:
            relative_path = "/" + relative.as_posix()
            
        data = {
            "name": path.name or self.root.name,
            "isDirectory": path.is_dir(),
            "path": relative_path,
            "updatedAt": stat.st_mtime,
            "size": stat.st_size if path.is_file() else 0,
        }
        
        if path.is_file():
            meta = self.read_metadata(path)
            if meta:
                data.update(meta)
                
        return data

    # ---------------------------------------------------------
    # LIST
    # ---------------------------------------------------------

    def get_children(self, relative_path: str = "/"):
        directory = self.safe_path(relative_path)

        if not directory.exists():
            raise HTTPException(
                status_code=404,
                detail="Path does not exist.",
            )

        if not directory.is_dir():
            raise HTTPException(
                status_code=400,
                detail="Path is not a directory.",
            )

        children = []

        for item in directory.iterdir():
            if item.name.startswith("."):
                continue

            if not item.is_file() and not item.is_dir():
                continue

            try:
                children.append(self.to_path(item))
            except OSError:
                continue

        # Folders first, then files
        children.sort(
            key=lambda item: (
                not item["isDirectory"],
                item["name"].lower(),
            )
        )

        return children

    # ---------------------------------------------------------
    # TREE
    # ---------------------------------------------------------

    def get_tree(self):
        directories = []
        def walk(current_dir):
            try:
                for item in current_dir.iterdir():
                    if item.is_dir():
                        try:
                            directories.append(self.to_path(item))
                            walk(item)
                        except OSError:
                            pass
            except OSError:
                pass
        
        walk(self.root)
        return directories

    # ---------------------------------------------------------
    # PARENT
    # ---------------------------------------------------------

    def get_parent(self, relative_path: str):
        current = self.safe_path(relative_path)

        if current == self.root:
            parent = self.root
        else:
            parent = current.parent

        return self.to_path(parent)

    # ---------------------------------------------------------
    # DOWNLOAD
    # ---------------------------------------------------------

    def get_file(self, relative_path: str) -> Path:
        file_path = self.safe_path(relative_path)

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found.",
            )

        if not file_path.is_file():
            raise HTTPException(
                status_code=400,
                detail="Path is not a file.",
            )

        return file_path

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def remove(self, relative_path: str):

        target = self.safe_path(relative_path)

        if target == self.root:
            raise HTTPException(
                status_code=403,
                detail="Cannot remove filesystem root.",
            )

        if not target.exists():
            raise HTTPException(
                status_code=404,
                detail="Path does not exist.",
            )

        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
            self.delete_metadata(target)

    # ---------------------------------------------------------
    # RENAME
    # ---------------------------------------------------------

    def rename(self, relative_path: str, new_name: str):

        source = self.safe_path(relative_path)

        if source == self.root:
            raise HTTPException(
                status_code=403,
                detail="Cannot rename root.",
            )

        if not source.exists():
            raise HTTPException(
                status_code=404,
                detail="Path does not exist.",
            )

        self.validate_name(new_name)

        destination = source.parent / new_name

        if destination.exists():
            raise HTTPException(
                status_code=409,
                detail="A file or folder with that name already exists.",
            )

        source.rename(destination)
        if source.is_file():
            meta_path = self.get_metadata_path(source)
            if meta_path.exists():
                meta_path.rename(self.get_metadata_path(destination))

    # ---------------------------------------------------------
    # CREATE DIRECTORY
    # ---------------------------------------------------------

    def mkdir(self, relative_path: str, name: str):

        directory = self.safe_path(relative_path)

        if not directory.exists():
            raise HTTPException(
                status_code=404,
                detail="Parent directory does not exist.",
            )

        if not directory.is_dir():
            raise HTTPException(
                status_code=400,
                detail="Parent is not a directory.",
            )

        self.validate_name(name)

        target = directory / name

        if target.exists():
            raise HTTPException(
                status_code=409,
                detail="Folder already exists.",
            )

        target.mkdir()

    # ---------------------------------------------------------
    # UPLOAD
    # ---------------------------------------------------------

    def save_upload(self, relative_path: str, filename: str, file):

        directory = self.safe_path(relative_path)

        if not directory.is_dir():
            raise HTTPException(
                status_code=400,
                detail="Upload destination is not a directory.",
            )

        filename = Path(filename).name

        self.validate_name(filename)

        destination = directory / filename
        
        self.delete_metadata(destination)

        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        return self.to_path(destination)

    # ---------------------------------------------------------
    # COPY
    # ---------------------------------------------------------

    def copy(self, source_path: str, destination_path: str):

        source = self.safe_path(source_path)
        destination = self.safe_path(destination_path)

        if not source.exists():
            raise HTTPException(
                status_code=404,
                detail="Source does not exist.",
            )

        if not destination.is_dir():
            raise HTTPException(
                status_code=400,
                detail="Destination must be a directory.",
            )

        target = destination / source.name

        if target.exists():
            raise HTTPException(
                status_code=409,
                detail="Destination already contains an item with this name.",
            )

        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
            meta_path = self.get_metadata_path(source)
            if meta_path.exists():
                shutil.copy2(meta_path, self.get_metadata_path(target))

    # ---------------------------------------------------------
    # MOVE
    # ---------------------------------------------------------

    def move(self, source_path: str, destination_path: str):

        source = self.safe_path(source_path)
        destination = self.safe_path(destination_path)

        if not source.exists():
            raise HTTPException(
                status_code=404,
                detail="Source does not exist.",
            )

        if not destination.is_dir():
            raise HTTPException(
                status_code=400,
                detail="Destination must be a directory.",
            )

        target = destination / source.name

        if target.exists():
            raise HTTPException(
                status_code=409,
                detail="Destination already contains an item with this name.",
            )

        # Prevent moving a directory inside itself
        if source.is_dir():
            try:
                destination.relative_to(source)
                raise HTTPException(
                    status_code=400,
                    detail="Cannot move a folder inside itself.",
                )
            except ValueError:
                pass

        shutil.move(str(source), str(target))
        if source.is_file():
            meta_path = self.get_metadata_path(source)
            if meta_path.exists():
                shutil.move(str(meta_path), str(self.get_metadata_path(target)))


filesystem = FileSystemService()