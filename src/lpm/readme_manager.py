"""README file management operations."""

from pathlib import Path

from .project import ProjectType


PYTHON_TEMPLATE = """# {project_name}

## Description

[Add a brief description of your project here]

## Installation

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```python
# Add usage examples here
```

## Dependencies

See `requirements.txt` or `pyproject.toml` for full list of dependencies.

## License

[Add license information]
"""

NODEJS_TEMPLATE = """# {project_name}

## Description

[Add a brief description of your project here]

## Installation

```bash
npm install
# or
yarn install
```

## Usage

```bash
npm start
# or
yarn start
```

## Scripts

- `npm start` - Start the application
- `npm test` - Run tests
- `npm run build` - Build for production

## License

[Add license information]
"""

RUST_TEMPLATE = """# {project_name}

## Description

[Add a brief description of your project here]

## Installation

```bash
cargo build
```

## Usage

```bash
cargo run
```

## Testing

```bash
cargo test
```

## License

[Add license information]
"""

GO_TEMPLATE = """# {project_name}

## Description

[Add a brief description of your project here]

## Installation

```bash
go build
```

## Usage

```bash
go run main.go
```

## Testing

```bash
go test ./...
```

## License

[Add license information]
"""

GENERIC_TEMPLATE = """# {project_name}

## Description

[Add a brief description of your project here]

## Usage

[Add usage instructions here]

## License

[Add license information]
"""


def get_readme_template(project_name: str, project_type: ProjectType) -> str:
    """
    Get README template based on project type.

    Args:
        project_name: Name of the project
        project_type: Type of project

    Returns:
        Formatted README template string
    """
    template_map = {
        ProjectType.PYTHON: PYTHON_TEMPLATE,
        ProjectType.NODEJS: NODEJS_TEMPLATE,
        ProjectType.RUST: RUST_TEMPLATE,
        ProjectType.GO: GO_TEMPLATE,
    }

    template = template_map.get(project_type, GENERIC_TEMPLATE)
    return template.format(project_name=project_name)


def create_readme(
    project_path: Path,
    project_name: str,
    project_type: ProjectType,
) -> Path:
    """
    Create a new README.md file in the project directory.

    Args:
        project_path: Path to project directory
        project_name: Name of the project
        project_type: Type of project

    Returns:
        Path to created README file

    Raises:
        FileExistsError: If README.md already exists
    """
    readme_path = project_path / "README.md"

    if readme_path.exists():
        raise FileExistsError(f"README already exists at {readme_path}")

    content = get_readme_template(project_name, project_type)
    readme_path.write_text(content)

    return readme_path


def read_readme(readme_path: Path) -> str:
    """
    Read content from README file.

    Args:
        readme_path: Path to README file

    Returns:
        README content as string

    Raises:
        FileNotFoundError: If README doesn't exist
    """
    if not readme_path.exists():
        raise FileNotFoundError(f"README not found at {readme_path}")

    return readme_path.read_text()


def view_readme(readme_path: Path) -> str:
    """
    View README content (formatted for display).

    Args:
        readme_path: Path to README file

    Returns:
        Formatted README content for viewing
    """
    return read_readme(readme_path)


def delete_readme(readme_path: Path) -> None:
    """
    Delete README file.

    Args:
        readme_path: Path to README file

    Raises:
        FileNotFoundError: If README doesn't exist
    """
    if not readme_path.exists():
        raise FileNotFoundError(f"README not found at {readme_path}")

    readme_path.unlink()
