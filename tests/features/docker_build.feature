Feature: Docker image build and usage

  Scenario: Docker image builds successfully
    Given Docker is available
    When the Docker image is built
    Then the image build should succeed
    And the image should contain all required tools

  Scenario: Docker command execution works
    Given Docker is available
    And the Docker image exists
    And the Python file "test_file.py" exists
    When taidy docker is called with the files
    Then the output should contain "Running:"