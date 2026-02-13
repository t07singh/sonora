"""
Test Docker Configuration

Tests that Docker configuration files are valid and complete.
"""

import os
import yaml
from pathlib import Path


class TestDockerConfig:
    """Test Docker configuration files."""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and has required content."""
        dockerfile_path = Path("Dockerfile")
        assert dockerfile_path.exists(), "Dockerfile should exist"
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check for required Dockerfile components
        assert "FROM python:3.11-slim" in content, "Should use Python 3.11 slim base"
        assert "WORKDIR /app" in content, "Should set working directory"
        assert "COPY . ." in content, "Should copy application files"
        assert "RUN pip install -r sonora/requirements.txt" in content, "Should install requirements"
        assert "EXPOSE 8000 8501" in content, "Should expose required ports"
        assert "uvicorn sonora.api.server:app" in content, "Should start FastAPI server"
        assert "streamlit run sonora/ui/app.py" in content, "Should start Streamlit UI"
    
    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists and is valid."""
        compose_path = Path("docker-compose.yml")
        assert compose_path.exists(), "docker-compose.yml should exist"
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Parse YAML to ensure it's valid
        try:
            compose_config = yaml.safe_load(content)
        except yaml.YAMLError as e:
            pytest.fail(f"docker-compose.yml is not valid YAML: {e}")
        
        # Check required services
        assert "services" in compose_config, "Should have services section"
        assert "sonora" in compose_config["services"], "Should have sonora service"
        
        sonora_service = compose_config["services"]["sonora"]
        assert "build" in sonora_service, "Should have build configuration"
        assert "ports" in sonora_service, "Should have port mappings"
        assert "env_file" in sonora_service, "Should have environment file configuration"
        
        # Check port mappings
        ports = sonora_service["ports"]
        assert "8000:8000" in ports, "Should map port 8000"
        assert "8501:8501" in ports, "Should map port 8501"
        
        # Check environment file
        assert sonora_service["env_file"] == [".env"], "Should use .env file"
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists in sonora directory."""
        requirements_path = Path("sonora/requirements.txt")
        assert requirements_path.exists(), "requirements.txt should exist in sonora directory"
        
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        # Check for key dependencies
        required_deps = [
            "fastapi",
            "uvicorn",
            "streamlit",
            "openai",
            "elevenlabs",
            "librosa",
            "soundfile",
            "pydub",
            "numpy"
        ]
        
        for dep in required_deps:
            assert dep in content.lower(), f"Should include {dep} dependency"
    
    def test_docker_ignore_exists(self):
        """Test that .dockerignore exists (optional but recommended)."""
        dockerignore_path = Path(".dockerignore")
        if dockerignore_path.exists():
            with open(dockerignore_path, 'r') as f:
                content = f.read()
            
            # Check for common ignore patterns
            ignore_patterns = ["__pycache__", ".git", "*.pyc", ".env"]
            for pattern in ignore_patterns:
                if pattern in content:
                    break
            else:
                # If none of the common patterns are found, that's okay
                # but we should at least have some ignore patterns
                assert len(content.strip()) > 0, "Should have some ignore patterns"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])










